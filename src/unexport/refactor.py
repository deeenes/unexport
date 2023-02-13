from __future__ import annotations

import ast
from typing import NamedTuple
import re

__all__ = ("refactor_source",)


class _Location(NamedTuple):
    start: int = 0
    end: int = 0
    all_exists: bool = False


def _find_location(source: str) -> _Location:
    location = _Location()
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, ast.Assign) and
            getattr(node.targets[0], "id", None) == "__all__"
        ):

            return location._replace(
                start=node.lineno - 1,
                end=node.end_lineno or 0,
                all_exists=True,
            )
        elif (
            isinstance(node, (ast.Import, ast.ImportFrom)) and
            node.lineno > location.start
        ):
            location = location._replace(start=node.end_lineno or 0)
    return location


def format_all(
        expected_all: list[str],
        long_lines: bool = False,
        single_quotes: bool = False,
    ) -> str:

    if not expected_all:
        return ''

    relinebreak = re.compile(r'([\[,]) ?')

    formatted_all = expected_all
    if not long_lines:
        formatted_all = relinebreak.sub('\\1\n    ', str(expected_all))[:-1]
        ending = ']\n' if long_lines else ',\n]\n'
    if single_quotes:
        formatted_all = formatted_all.replace('"', "'")
    formatted_all = f"{formatted_all}{ending}"
    formatted_all = f"__all__ = {formatted_all}"

    return formatted_all


def refactor_source(
        source: str,
        expected_all: list[str],
        long_lines: bool = False,
        single_quotes: bool = False,
    ) -> str:

    if not expected_all:
        return source

    location = _find_location(source)
    lines = ast._splitlines_no_ff(source)  # type: ignore

    if location.all_exists:
        if location.start != location.end:
            del lines[location.start : location.end]
        else:
            del lines[location.start]

    formatted_all = format_all(
        expected_all,
        long_lines=long_lines,
        single_quotes=single_quotes,
    )
    lines.insert(location.start, formatted_all)

    next_line = lines[location.start + 1]
    previous_line = lines[location.start - 1]
    if next_line != "\n":
        lines.insert(location.start + 1, "\n")
    if location.start != 0 and previous_line != "\n":
        lines.insert(location.start, "\n")
    return "".join(lines)
