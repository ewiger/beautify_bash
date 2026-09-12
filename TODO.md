# TODO

## Correctness

- [ ] Replace the line-and-regex approach with a real tokenizer. The current
      one cannot see a construct that spans lines other than here-docs and
      quotes (e.g. a `case` arm split across lines, or `if` continued with
      a trailing `\`).
- [ ] Line continuations (`\` at end of line): the continuation line should be
      indented as a continuation, not as a new statement.
- [ ] Multiple here-docs opened on one line (`cmd <<A <<B`) — only the first
      tag is tracked.
- [ ] Here-doc tags that are not plain words (e.g. `<<$var`); tags quoted
      with `'`, `"` or `\` and tags containing `-`/`.` already work.
- [ ] `$( … )` and `${ … }` spanning lines are counted as bare brackets.
- [ ] Arithmetic `(( … ))` and `[[ … ]]` are counted as two brackets each;
      correct today by symmetry, wrong if one side is inside a string.
- [ ] `;&` and `;;&` case fallthrough (bash 4) are not treated as branch ends.
- [ ] `select … do … done` and `until … do … done` work by accident via `do`;
      cover them with tests.

## Features

- [ ] `--stdin-filename` so `--diff` and dialect detection get a real name when
      reading stdin (mirrors `black`).
- [ ] Align trailing comments and `\` continuations as an opt-in pass.
- [ ] Optional normalisation of `function f {` vs `f() {`.
- [ ] Blank-line policy: collapse runs of blank lines, enforce one before
      top-level function definitions.
- [ ] Emit a `# shellcheck`-compatible machine-readable error format.
- [ ] `--config` / `pyproject.toml` `[tool.beautify-bash]` section.
- [ ] Editor integrations: a `pre-commit` hook repo and an LSP formatting
      provider.

## Dialects

- [ ] `ksh` (co-processes, `function` blocks).
- [ ] `fish` (`if`/`end`, `switch`/`case`/`end`, `function`/`end`) — the block
      model is different enough that it needs its own close-keyword handling.
- [ ] `dash` / strict POSIX mode that warns on bashisms rather than formatting
      them.

## Infrastructure

- [ ] Publish to PyPI and wire up trusted publishing from CI.
- [ ] Property-based tests (Hypothesis): formatting is idempotent, and the
      token stream is unchanged by formatting.
- [ ] A corpus test that runs the formatter over a set of real-world scripts
      and asserts `bash -n` still accepts the output.
- [ ] Raise coverage to 100% and gate on it in CI.
