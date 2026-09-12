# Changelog

## 2.0.0

First release published to PyPI. The 1.x versions were only ever distributed as
a single script from [arachnoid.com][arachnoid], so this is the first
installable package.

- Proper `src/` package layout with type hints and a `py.typed` marker.
- A [Typer][typer] command line interface: `--check`, `--diff`, `--version`,
  stdin/stdout, and in-place formatting of multiple files.
- Shell dialect support (`bash`, `zsh`) with detection from the shebang and the
  file extension.
- A public Python API: `beautify_string`, `Beautifier`, `FormatResult`.
- Tested on CPython 3.9 through 3.14 on Linux and macOS.

[arachnoid]: http://arachnoid.com/python/beautify_bash_program.html
[typer]: https://typer.tiangolo.com/
