"""Recognize bounded T3 wrappers used for one or more tool calls."""

from __future__ import annotations

import json
import re
from typing import Any, Literal, NamedTuple


MAX_EXEC_WRAPPER_SOURCE_LENGTH = 20_000
MAX_EXEC_OBJECT_LITERAL_LENGTH = 8_000
MAX_EXEC_OBJECT_NESTING_DEPTH = 8
MAX_EXEC_COMMAND_LENGTH = 4_000
MAX_EXEC_TRAILER_NESTING_DEPTH = 12
MAX_EXEC_TRAILER_TOKENS = 256


class ScannedToolCall(NamedTuple):
    """One tools.<name>(<object literal>) call anchored at a known position."""

    name: str
    object_literal: str
    end: int


class ExecWrapperResult(NamedTuple):
    """Outcome of the strict, position-anchored T3 exec wrapper recognizer."""

    status: Literal["recognized", "unsupported", "malformed"]
    command: str | None
    callee: str | None = None


class ExecBatchResult(NamedTuple):
    """Outcome of the position-anchored Promise.all wrapper recognizer."""

    status: Literal["recognized", "unsupported", "malformed"]
    commands: list[str] | None
    callee: str | None = None


class ExecWrapperAttribution(NamedTuple):
    """Everything one T3 `exec` wrapper contributes to a snapshot."""

    callee: str | None
    commands: list[str] | None
    coverage_bucket: str | None


class LexicalToolCalls(NamedTuple):
    """Tool call sites found outside JavaScript strings and comments."""

    first: str | None
    has_exec_command: bool


class _ExpressionToken(NamedTuple):
    kind: Literal["identifier", "literal", "punctuator"]
    value: str


class _ExecCommandTooLong(Exception):
    pass


_EXEC_ASSIGNMENT_PREFIX_RE = re.compile(r"\s*(?:const|let)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*await\s+")
_BATCH_ASSIGNMENT_PREFIX_RE = re.compile(
    r"\s*(?:const|let)\s+(?:"
    r"[A-Za-z_$][A-Za-z0-9_$]*|"
    r"\[\s*[A-Za-z_$][A-Za-z0-9_$]*(?:\s*,\s*[A-Za-z_$][A-Za-z0-9_$]*)*\s*,?\s*\]"
    r")\s*=\s*await\s+Promise\.all\s*\(\s*\["
)
_TOOLS_CALL_RE = re.compile(r"tools\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
# The site patterns are searched over a whole wrapper rather than matched at a known
# position, so they require something a call can follow. A patch body that adds
# `tools.find(` is text, not a call site, and must not name a per-tool row.
_CALL_POSITION = r"(?:await|[\[,(]|=>|^|\n)\s*"
_TOOLS_CALL_SITE_RE = re.compile(_CALL_POSITION + r"tools\.([A-Za-z_$][A-Za-z0-9_$]*)\s*\(")
_CLOSE_PAREN_RE = re.compile(r"\s*\)")
_TEXT_CALL_RE = re.compile(r"text\s*\(")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUMBER_RE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_JSON_VALUE_DECODER = json.JSONDecoder()
_BINARY_OPERATORS = {
    "||": 1,
    "??": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "===": 3,
    "!==": 3,
    "<": 4,
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "%": 6,
}
_PUNCTUATORS = tuple(sorted((*_BINARY_OPERATORS, "!", "?", ":", ".", "(", ")", "{", "}", ","), key=len, reverse=True))


def _skip_ws(text: str, pos: int, end: int) -> int:
    while pos < end and text[pos] in " \t\r\n":
        pos += 1
    return pos


def _scan_quoted_string(text: str, start: int, limit: int) -> int | None:
    quote = text[start]
    index = start + 1
    while index < len(text) and index < limit:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        if quote != "`" and char in "\r\n":
            return None
        index += 1
    return None


def _lexical_tool_calls(source: str) -> LexicalToolCalls:
    """Find bounded tool call sites after hiding strings and comments."""
    limit = min(len(source), MAX_EXEC_WRAPPER_SOURCE_LENGTH)
    masked = list(source[:limit])
    index = 0

    def hide(start: int, end: int) -> None:
        for position in range(start, end):
            if masked[position] not in "\r\n":
                masked[position] = " "

    while index < limit:
        if source[index] in "'\"`":
            end = _scan_quoted_string(source, index, limit) or limit
            hide(index, end)
            index = end
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2, limit)
            end = limit if newline == -1 else newline
            hide(index, end)
            index = end
            continue
        if source.startswith("/*", index):
            close = source.find("*/", index + 2, limit)
            end = limit if close == -1 else close + 2
            hide(index, end)
            index = end
            continue
        index += 1

    first: str | None = None
    has_exec_command = False
    for match in _TOOLS_CALL_SITE_RE.finditer("".join(masked)):
        name = match.group(1)
        if first is None:
            first = name
        if name == "exec_command":
            has_exec_command = True
    return LexicalToolCalls(first, has_exec_command)


def _scan_balanced(text: str, start: int, max_length: int, max_depth: int) -> int | None:
    """Return the position after the matching delimiter within both hard limits."""
    pairs = {"{": "}", "[": "]", "(": ")"}
    if start >= len(text) or text[start] not in pairs:
        return None
    stack: list[str] = []
    index = start
    limit = min(len(text), start + max_length)
    while index < limit:
        char = text[index]
        if char in "'\"`":
            string_end = _scan_quoted_string(text, index, limit)
            if string_end is None:
                return None
            index = string_end
            continue
        if char in pairs:
            stack.append(pairs[char])
            if len(stack) > max_depth:
                return None
        elif char in "}])":
            if not stack or char != stack.pop():
                return None
            if not stack:
                return index + 1
        index += 1
    return None


def _reject_oversized_string(text: str, pos: int, max_length: int) -> None:
    limit = pos + max_length + 1
    index = pos + 1
    while index < len(text):
        if index > limit:
            raise _ExecCommandTooLong()
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == '"':
            return
        index += 1


def scan_tool_call(source: str, position: int) -> ScannedToolCall | None:
    """Match tools.<name>(<object literal>) at position after leading whitespace."""
    pos = _skip_ws(source, position, len(source))
    match = _TOOLS_CALL_RE.match(source, pos)
    if match is None:
        return None
    object_start = _skip_ws(source, match.end(), len(source))
    if object_start >= len(source) or source[object_start] != "{":
        return None
    object_end = _scan_balanced(
        source,
        object_start,
        MAX_EXEC_OBJECT_LITERAL_LENGTH,
        MAX_EXEC_OBJECT_NESTING_DEPTH,
    )
    if object_end is None:
        return None
    close_match = _CLOSE_PAREN_RE.match(source, object_end)
    if close_match is None:
        return None
    return ScannedToolCall(match.group(1), source[object_start:object_end], close_match.end())


def _parse_object_literal(text: str) -> dict[str, Any] | None:
    end = len(text)
    if end == 0 or text[0] != "{":
        return None
    pos = _skip_ws(text, 1, end)
    result: dict[str, Any] = {}
    if pos < end and text[pos] == "}":
        return result if pos + 1 == end else None
    while True:
        pos = _skip_ws(text, pos, end)
        if pos >= end:
            return None
        if text[pos] == '"':
            try:
                key, pos = _JSON_VALUE_DECODER.raw_decode(text, pos)
            except json.JSONDecodeError:
                return None
            if not isinstance(key, str):
                return None
        else:
            match = _IDENTIFIER_RE.match(text, pos)
            if match is None:
                return None
            key, pos = match.group(0), match.end()
        if key in result:
            return None
        pos = _skip_ws(text, pos, end)
        if pos >= end or text[pos] != ":":
            return None
        pos = _skip_ws(text, pos + 1, end)
        if pos >= end:
            return None
        if key == "cmd" and text[pos] == '"':
            _reject_oversized_string(text, pos, MAX_EXEC_COMMAND_LENGTH)
        try:
            value, pos = _JSON_VALUE_DECODER.raw_decode(text, pos)
        except json.JSONDecodeError:
            return None
        result[key] = value
        pos = _skip_ws(text, pos, end)
        if pos >= end:
            return None
        if text[pos] == ",":
            pos = _skip_ws(text, pos + 1, end)
            if pos < end and text[pos] == "}":
                return None
            continue
        if text[pos] == "}":
            return result if pos + 1 == end else None
        return None


def _tokenize_expression(text: str) -> list[_ExpressionToken] | None:
    tokens: list[_ExpressionToken] = []
    pos = 0
    while True:
        pos = _skip_ws(text, pos, len(text))
        if pos >= len(text):
            return tokens
        if text[pos] == '"':
            try:
                value, end = _JSON_VALUE_DECODER.raw_decode(text, pos)
            except json.JSONDecodeError:
                return None
            if not isinstance(value, str):
                return None
            tokens.append(_ExpressionToken("literal", text[pos:end]))
            pos = end
            continue
        number_match = _NUMBER_RE.match(text, pos)
        if number_match is not None:
            tokens.append(_ExpressionToken("literal", number_match.group(0)))
            pos = number_match.end()
            continue
        identifier_match = _IDENTIFIER_RE.match(text, pos)
        if identifier_match is not None:
            tokens.append(_ExpressionToken("identifier", identifier_match.group(0)))
            pos = identifier_match.end()
            continue
        punctuator = next((candidate for candidate in _PUNCTUATORS if text.startswith(candidate, pos)), None)
        if punctuator is None:
            return None
        tokens.append(_ExpressionToken("punctuator", punctuator))
        pos += len(punctuator)


class _SafeExpressionParser:
    def __init__(self, tokens: list[_ExpressionToken], result_identifier: str):
        self.tokens = tokens
        self.result_identifier = result_identifier
        self.pos = 0

    def parse(self) -> tuple[bool, bool]:
        valid, referenced = self._parse_conditional()
        return valid and self.pos == len(self.tokens), referenced

    def _peek(self, value: str | None = None) -> _ExpressionToken | None:
        if self.pos >= len(self.tokens):
            return None
        token = self.tokens[self.pos]
        return token if value is None or token.value == value else None

    def _consume(self, value: str | None = None) -> _ExpressionToken | None:
        token = self._peek(value)
        if token is not None:
            self.pos += 1
        return token

    def _parse_conditional(self) -> tuple[bool, bool]:
        valid, referenced = self._parse_binary(1)
        if not valid or self._consume("?") is None:
            return valid, referenced
        true_valid, true_referenced = self._parse_conditional()
        if not true_valid or self._consume(":") is None:
            return False, False
        false_valid, false_referenced = self._parse_conditional()
        return false_valid, referenced or true_referenced or false_referenced

    def _parse_binary(self, minimum_precedence: int) -> tuple[bool, bool]:
        valid, referenced = self._parse_unary()
        if not valid:
            return False, False
        while True:
            token = self._peek()
            precedence = _BINARY_OPERATORS.get(token.value) if token is not None else None
            if precedence is None or precedence < minimum_precedence:
                return True, referenced
            self.pos += 1
            right_valid, right_referenced = self._parse_binary(precedence + 1)
            if not right_valid:
                return False, False
            referenced = referenced or right_referenced

    def _parse_unary(self) -> tuple[bool, bool]:
        while self._peek() is not None and self._peek().value in {"!", "+", "-"}:
            self.pos += 1
        return self._parse_primary()

    def _parse_primary(self) -> tuple[bool, bool]:
        token = self._consume()
        if token is None:
            return False, False
        if token.kind == "literal":
            return True, False
        if token.value in {"true", "false", "null", "undefined"}:
            return True, False
        if token.value == self.result_identifier:
            while self._consume(".") is not None:
                member = self._consume()
                if member is None or member.kind != "identifier":
                    return False, False
            return True, True
        if token.value == "JSON":
            if self._consume(".") is None or self._consume("stringify") is None or self._consume("(") is None:
                return False, False
            valid, referenced = self._parse_conditional()
            return (self._consume(")") is not None, referenced) if valid else (False, False)
        if token.value == "(":
            valid, referenced = self._parse_conditional()
            return (self._consume(")") is not None, referenced) if valid else (False, False)
        if token.value == "{":
            return self._parse_object()
        return False, False

    def _parse_object(self) -> tuple[bool, bool]:
        referenced = False
        if self._consume("}") is not None:
            return True, False
        while True:
            key = self._consume()
            if key is None or key.kind not in {"identifier", "literal"} or self._consume(":") is None:
                return False, False
            valid, value_referenced = self._parse_conditional()
            if not valid:
                return False, False
            referenced = referenced or value_referenced
            if self._consume("}") is not None:
                return True, referenced
            if self._consume(",") is None or self._peek("}") is not None:
                return False, False


def _validate_text_argument(argument: str, identifier: str) -> tuple[bool, bool]:
    tokens = _tokenize_expression(argument)
    if not tokens or len(tokens) > MAX_EXEC_TRAILER_TOKENS:
        return False, False
    return _SafeExpressionParser(tokens, identifier).parse()


def _validate_text_trailer(trailer: str, identifier: str) -> bool:
    pos = 0
    found_call = False
    referenced = False
    while True:
        pos = _skip_ws(trailer, pos, len(trailer))
        if pos >= len(trailer):
            break
        match = _TEXT_CALL_RE.match(trailer, pos)
        if match is None:
            return False
        open_paren = match.end() - 1
        close_pos = _scan_balanced(
            trailer,
            open_paren,
            MAX_EXEC_WRAPPER_SOURCE_LENGTH,
            MAX_EXEC_TRAILER_NESTING_DEPTH,
        )
        if close_pos is None:
            return False
        valid, call_referenced = _validate_text_argument(trailer[open_paren + 1 : close_pos - 1], identifier)
        if not valid:
            return False
        found_call = True
        referenced = referenced or call_referenced

        whitespace_start = close_pos
        next_pos = _skip_ws(trailer, close_pos, len(trailer))
        if next_pos < len(trailer) and trailer[next_pos] == ";":
            pos = next_pos + 1
            continue
        if next_pos >= len(trailer):
            pos = next_pos
            continue
        if "\n" not in trailer[whitespace_start:next_pos] and "\r" not in trailer[whitespace_start:next_pos]:
            return False
        pos = next_pos
    return found_call and referenced


def _recognize_exec_wrapper(source: str) -> ExecWrapperResult:
    if len(source) > MAX_EXEC_WRAPPER_SOURCE_LENGTH:
        return ExecWrapperResult("unsupported", None)
    prefix_match = _EXEC_ASSIGNMENT_PREFIX_RE.match(source)
    if prefix_match is None:
        return ExecWrapperResult("unsupported", None)
    scanned = scan_tool_call(source, prefix_match.end())
    if scanned is None or scanned.name != "exec_command":
        return ExecWrapperResult("unsupported", None)
    parsed = _parse_object_literal(scanned.object_literal)
    if parsed is None:
        return ExecWrapperResult("malformed", None)
    command = parsed.get("cmd")
    if not isinstance(command, str):
        return ExecWrapperResult("malformed", None)
    separator_start = scanned.end
    pos = _skip_ws(source, separator_start, len(source))
    if pos < len(source) and source[pos] == ";":
        pos += 1
    elif pos < len(source) and "\n" not in source[separator_start:pos] and "\r" not in source[separator_start:pos]:
        return ExecWrapperResult("unsupported", None)
    if not _validate_text_trailer(source[pos:], prefix_match.group(1)):
        return ExecWrapperResult("unsupported", None)
    return ExecWrapperResult("recognized", command, scanned.name)


def recognize_exec_wrapper(source: str) -> ExecWrapperResult:
    """Recognize one exec_command assignment followed only by safe text calls."""
    try:
        return _recognize_exec_wrapper(source)
    except (_ExecCommandTooLong, RecursionError, ValueError):
        return ExecWrapperResult("unsupported", None)


def _recognize_exec_batch(source: str) -> ExecBatchResult:
    if len(source) > MAX_EXEC_WRAPPER_SOURCE_LENGTH:
        return ExecBatchResult("unsupported", None)
    prefix_match = _BATCH_ASSIGNMENT_PREFIX_RE.match(source)
    if prefix_match is None:
        return ExecBatchResult("unsupported", None)

    commands: list[str] = []
    pos = prefix_match.end()
    callee: str | None = None
    while True:
        pos = _skip_ws(source, pos, len(source))
        if pos >= len(source):
            return ExecBatchResult("unsupported", None)
        if source[pos] == "]":
            if callee is None:
                return ExecBatchResult("unsupported", None)
            trailer = source[pos + 1 :]
            # A batch trailer has a deliberately weaker rule than a single-call
            # trailer. The element scan has already reached the closing bracket,
            # so the trailer only needs to prove that no later tool call ran.
            if "tools." in trailer:
                return ExecBatchResult("unsupported", None)
            return ExecBatchResult("recognized", commands, callee)

        scanned = scan_tool_call(source, pos)
        if scanned is None:
            return ExecBatchResult("unsupported", None)
        parsed = _parse_object_literal(scanned.object_literal)
        if parsed is None:
            return ExecBatchResult("malformed", None)
        if scanned.name == "exec_command":
            command = parsed.get("cmd")
            if not isinstance(command, str):
                return ExecBatchResult("malformed", None)
            commands.append(command)
        if callee is None:
            callee = scanned.name
        pos = _skip_ws(source, scanned.end, len(source))
        if pos >= len(source):
            return ExecBatchResult("unsupported", None)
        if source[pos] == ",":
            pos += 1
            continue
        if source[pos] != "]":
            return ExecBatchResult("unsupported", None)


def recognize_exec_batch(source: str) -> ExecBatchResult:
    """Recognize a Promise.all array of plain tools.<name> object-literal calls."""
    try:
        return _recognize_exec_batch(source)
    except (_ExecCommandTooLong, RecursionError, ValueError):
        return ExecBatchResult("unsupported", None)


def attribute_exec_wrapper(source: str) -> ExecWrapperAttribution:
    """Read a wrapper once for every label a snapshot needs from it.

    The callee of record is the tool the wrapper actually called. It comes from the
    recognizer's own parse when that succeeded, and from a lexical scan for the first
    `tools.<name>(` call site otherwise. The scan only groups and buckets; it never
    labels a command, so its worst failure is a miscounted row.
    """
    single = recognize_exec_wrapper(source)
    if single.status == "recognized" and single.command is not None:
        return ExecWrapperAttribution(single.callee, [single.command], None)
    batch = recognize_exec_batch(source)
    if batch.status == "recognized":
        return ExecWrapperAttribution(batch.callee, batch.commands or None, None)
    call_sites = _lexical_tool_calls(source)
    if call_sites.has_exec_command:
        return ExecWrapperAttribution(call_sites.first, None, "unreadable_shell_wrappers")
    if call_sites.first is None:
        return ExecWrapperAttribution(None, None, "unparsed_wrappers")
    return ExecWrapperAttribution(call_sites.first, None, None)
