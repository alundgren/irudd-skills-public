---
name: next-issue
description: Select and immediately launch the next eligible GitHub issue in the current checkout, optionally filtered by a plain-language epic focus. Use when the user asks what issue to work on next or asks to start the next ready issue.
license: MIT
---

# Select and launch the next eligible issue

Use this skill only to choose work from the repository of the current
checkout. Never enumerate another accessible repository, and never claim,
edit, comment on, or otherwise modify an issue in this skill.

An optional user-supplied focus is plain language, for example “the billing
epic”. It narrows selection; it is not permission to relax any eligibility
gate.

## 1. Discover a bounded, metadata-only candidate set

Resolve the current checkout's `origin` remote to an exact GitHub
`OWNER/REPO`. Stop and ask the user if it is not a GitHub repository or cannot
be resolved unambiguously. Calculate the calendar date two months before
invocation in `YYYY-MM-DD` form.

Run one bounded issue search against **that repository only**. Request no
issue or epic bodies during this scan:

```sh
gh issue list --repo OWNER/REPO --state open --label ready-for-agent \
  --search "updated:>=YYYY-MM-DD -label:claimed sort:updated-desc" --limit 500 \
  --json number,title,url,labels,createdAt,updatedAt,parent,blockedBy,blocking
```

Treat the returned records as the complete candidate set. If exactly 500
records were examined, mark the discovery as capped. Do not fetch a next page
or broaden the search.

The search is only a narrowing step. Independently verify on every returned
record that it is open, has `ready-for-agent`, lacks `claimed`, and has
`updatedAt` on or after the calculated date. This preserves the hard gate even
if GitHub search semantics change.

For dependency data, use native GitHub issue relationships only. Inspect the
returned `blockedBy` and `blocking` nodes and their states. If either
relationship connection is paginated, incomplete, or lacks the state needed
to decide, page that connection for that candidate with GitHub's native API
until it is complete. Request only issue number and state (and title only
where needed for the optional focus); never request a body. Do not decide
eligibility or ranking from partial dependency data, markdown prose, task
lists, or issue text.

## 2. Apply focus, eligibility, and deterministic ranking

An issue is eligible only when all of these remain true:

- it is open;
- it has `ready-for-agent` and not `claimed`;
- it has zero `blockedBy` issues whose native state is open.

With a focus, retain only eligible candidates whose own title or immediate
parent epic title materially matches the focus. Compare only those titles; do
not fetch candidate or parent bodies, and do not infer focus from labels or
other relationships. A parent title may be read from the `parent` metadata.

For each remaining candidate, count its direct `blocking` issues whose native
state is open. Sort candidates by:

1. More open direct issues blocked.
2. Earlier `createdAt`.
3. Lower issue number.

If no candidate remains, respond with exactly:

```
No issues to work on found.
```

Do not add explanatory text and do not make a GitHub mutation in that case.

Otherwise, briefly state the selected issue's number, title, URL, count of
open direct issues it blocks, creation time, and the applied focus when there
was one. If discovery was capped, also say `Discovery list was capped at 500
records.`

## 3. Immediately dispatch; do not implement here

Do **not** add `claimed`: the receiving implementation skill owns its fresh
claim gate and implementation. In the same session, invoke `implement-issue`
with the exact `OWNER/REPO` and selected issue number in every supported
runtime.

State the repository and issue number explicitly in the handoff. The receiving
skill must revalidate the issue, add `claimed` if eligible, and preserve its
normal stop behavior if its claim gate fails. Do not replace that workflow
with a local implementation, an independent claim, or a cross-repository
lookup.
