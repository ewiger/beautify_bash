# beautify_bash

A code formatter / beautifier for **bash** and **zsh** shell scripts.

Originally written in Ruby, then Python, by [Paul Lutus][arachnoid]; revived
here with a proper package layout, a [Typer][typer] CLI, [uv][uv] tooling,
a test suite, and support for shell dialects.

[arachnoid]: http://arachnoid.com/python/beautify_bash_program.html
[typer]: https://typer.tiangolo.com/
[uv]: https://docs.astral.sh/uv/

## Install

```bash
uv tool install beautify-bash      # as a standalone command
uv add beautify-bash               # as a project dependency
pipx install beautify-bash         # or with pipx
```

Run it without installing:

```bash
uvx beautify-bash script.sh
```

Requires Python 3.9 or newer (tested through 3.14).

## Use

Like `shfmt` and `gofmt`, it prints to standard output and changes nothing on
disk unless you ask it to:

```bash
beautify-bash script.sh                 # print the formatted script
beautify-bash -w script.sh              # rewrite in place, keeping script.sh~
beautify-bash -w --no-backup script.sh  # rewrite without a backup
beautify-bash -o tidy.sh script.sh      # write the result to another file
beautify-bash --check src/*.sh          # exit 1 if anything would change (CI)
beautify-bash --diff script.sh          # show a unified diff, write nothing
beautify-bash --indent 4 script.sh      # four spaces per level
beautify-bash --tabs script.sh          # indent with tabs
beautify-bash -d zsh script.zsh         # force a dialect
cat script.sh | beautify-bash -         # stdin to stdout
beautify-bash -w src/*.sh               # format a whole directory
python -m beautify_bash script.sh       # same thing via the module
```

Standard output carries only the formatted script; progress notes, diffs of
the `--check` kind, and errors go to standard error, so `beautify-bash x.sh >
y.sh` is safe.

### Options

| Option | Meaning |
| --- | --- |
| *(none)* | Print the formatted script to stdout; several inputs are concatenated. |
| `-w`, `--write` | Rewrite each input file in place. |
| `-o`, `--output PATH` | Write the result to `PATH` (`-` means stdout). |
| `-i`, `--indent N` | Spaces per indentation level (default `2`). |
| `--tabs` / `--spaces` | Indent with tab characters instead of spaces. |
| `-d`, `--dialect` | `auto` (default), `bash`, or `zsh`. |
| `--check` | Write nothing; exit `1` if a file would change. |
| `--diff` | Print a unified diff instead of writing. |
| `--backup` / `--no-backup` | With `-w`, keep the original as `FILE~` (default on). |
| `-q`, `--quiet` | Suppress per-file progress notes. |
| `-V`, `--version` | Print the version and exit. |

`-w`, `-o`, `--check` and `--diff` are mutually exclusive, and `-w` cannot
rewrite standard input.

Exit codes: `0` clean, `1` a file changed (under `--check`/`--diff`) or a
syntax problem was reported, `2` a file could not be read or written, or the
options conflict.

## Dialects

`--dialect auto` picks the dialect from the shebang line first, then the file
name (`.zsh`, `.zshrc`, `.zshenv`, …), and falls back to bash.

| Dialect | Block keywords |
| --- | --- |
| `bash` | `case`/`esac`, `if`/`then`/`elif`/`else`/`fi`, `do`/`done`, `{}`, `()`, `[]` |
| `zsh` | everything bash has, plus `foreach … end` and `} always {` |

Adding a shell means adding one `Dialect` instance in
[dialects.py](src/beautify_bash/dialects.py) — the indenter itself is dialect
agnostic.

## Library use

```python
from beautify_bash import ZSH, Beautifier, beautify_string

result = beautify_string(open("script.sh").read())
print(result.text)
print(result.dialect.name, result.ok, result.errors)

# Explicit configuration
tidy = Beautifier(indent_char="\t", indent_size=1, dialect=ZSH)
print(tidy.format("foreach f (a b)\nprint $f\nend").text)
```

The 1.x API (`BeautifyBash`, `beautify_string(data, path) -> (text, error)`,
`beautify_file`, `tab_str`, `tab_size`) still works.

## What is preserved verbatim

Re-indenting must never change what a script does, so these regions are passed
through byte for byte:

- here-document bodies (`<<EOF`, and `<<-EOF` with its indented terminator),
- lines inside a multi-line `'…'` or `"…"` string,
- everything inside comments and quotes is ignored for keyword counting.

Shell reserved words only count as keywords in *command position* — at the
start of a line or after `;`, `&`, `|`, or a bracket — so `echo done` no longer
dedents the following lines.

## Pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: beautify-bash
        name: beautify-bash
        entry: beautify-bash -w
        language: system
        types: [shell]
```

## Development

```bash
uv sync                     # create .venv and install dev dependencies
uv run pytest               # run the tests
uv run pytest --cov         # with coverage
uv run ruff check .         # lint
uv run ruff format .        # format the Python sources
uv run mypy                 # type check
```

The test suite is in [tests/](tests/):

- [test_beautifier.py](tests/test_beautifier.py) — the indenting core,
- [test_dialects.py](tests/test_dialects.py) — dialect detection and zsh syntax,
- [test_cli.py](tests/test_cli.py) — the CLI, via Typer's `CliRunner`,
- [test_mocks.py](tests/test_mocks.py) — worked `unittest.mock` examples
  (patching methods, `mock_open`, fake streams, spies, stubs, autospec).

## Roadmap

See [TODO.md](TODO.md).

## License

GPL-2.0-or-later. See [LICENSE](LICENSE).
