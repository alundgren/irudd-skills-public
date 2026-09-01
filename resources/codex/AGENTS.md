# Writing about software

When writing original content about software work, use direct, concrete
language.

- Do not use `seam`, `spine`, `shape`, `load-bearing`, or `blast radius`.
  This includes different casing, plurals, inflections, and compounds. The
  rule also applies to new names for functions, classes, variables, files,
  fields, and other code elements.
- Use one of those terms only when a human has explicitly given permission.
  Existing source material is different: use an exact existing name, literal,
  error, quote, or search term when the task requires it, but do not repeat it
  in your own explanation.
- Name the actual API, component, module, dependency, affected behaviour, or
  failure case. Explain the practical consequence instead of assigning an
  abstract label to it.
- Write as a senior engineer explaining the work to a junior engineer: clear,
  friendly, and direct. Do not write like a journal article, scientific paper,
  or technical reference manual.
- When a non-obvious risk or trade-off would be clearer with an example,
  prefer a short, specific example. For example, say that invoice `abc123`
  and invoice `abc1234` would both become `abc123` after truncation, causing a
  collision, instead of describing a generic possible identity problem.

# GitHub operations under a SANDBOXED NETWORK

Codex command sandboxes can lack network egress even when your GitHub
credentials are perfectly valid — in particular, the `read-only` sandbox has
no network access at all. A `gh` failure inside such a sandbox is not
automatically an authentication problem. Follow these defaults:

- Prefer the connected GitHub connector for the GitHub reads it supports; it
  does not depend on the command sandbox having network access.
- When shell `gh` is necessary and the current sandbox is known to lack
  egress, request the network-capable execution route immediately, with a
  truthful, narrowly scoped justification. Do not deliberately run a doomed
  sandbox preflight first.
- In Auto mode, let the harness's automatic reviewer handle eligible safe
  escalation requests; do not routinely interrupt the user for them.
- Classify safety from the complete operation — remote mutation, local
  filesystem effects, credential exposure, and the requested target — not
  merely from the executable being named `gh`. A `gh` read mutates nothing on
  GitHub but still needs network access and may write local files; a `gh`
  write additionally needs the user's authorization for the exact target and
  intended change.
- Perform GitHub writes only when the user authorized the exact target and
  intended change.
- Never expose authentication tokens. Do not run `gh auth token` or
  `gh auth status --show-token`, and do not print token values.
- Treat `gh`'s "The token in ... is invalid" message as ambiguous: the same
  text appears for DNS failures, dead proxies, and sandbox egress denial.
  Check network, proxy, and sandbox conditions before recommending
  reauthentication.
- Do not narrate internal escalation unless it becomes user-visible or blocks
  progress.
- Keep independent local validation independent: do not place a
  network-dependent auth check before unrelated local checks in one `&&`
  chain.
- More-specific repository instructions may override these global defaults
  explicitly.
