"""Regression tests for the requirements-file options Sphinx directive.

Covers https://github.com/pypa/pip/issues/14261: the
``pip-requirements-file-options-ref-list`` directive must emit one
well-formed MyST entry per option (with a valid source location), so the
gettext builder extracts per-option ``{ref}`` messages instead of a single
merged message with raw RST ``:ref:`` markup and broken ``file:line``
locations.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("sphinx")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs"))

import pip_sphinxext
from docutils import nodes
from docutils.statemachine import ViewList

from pip._internal.req.req_file import SUPPORTED_OPTIONS

SOURCE = "docs/html/reference/requirements-file-format.md"
MYST_ENTRY_RE = re.compile(r"^- \{ref\}`(.+) <([^`]+)>`$")


def _make_directive() -> pip_sphinxext.PipReqFileOptionsReference:
    state = SimpleNamespace(
        document=SimpleNamespace(current_source=SOURCE),
        nested_parse=lambda *args, **kwargs: None,
    )
    directive = pip_sphinxext.PipReqFileOptionsReference(
        name="pip-requirements-file-options-ref-list",
        arguments=[],
        options={},
        content=[],
        lineno=86,
        content_offset=0,
        block_text="",
        state=state,
        state_machine=SimpleNamespace(reporter=None),
    )
    directive.view_list = ViewList()
    return directive


def test_entries_are_per_option_myst_with_valid_source() -> None:
    directive = _make_directive()
    directive.process_options()

    lines = list(directive.view_list.data)
    sources = [source for source, _offset in directive.view_list.items]
    bullets = [line for line in lines if line.startswith("- ")]

    active_options = [
        o for o in SUPPORTED_OPTIONS if not getattr(o, "deprecated", False)
    ]
    assert len(bullets) == len(active_options)

    for line in bullets:
        assert ":ref:" not in line
        match = MYST_ENTRY_RE.match(line)
        assert match is not None, f"not a MyST ref entry: {line!r}"

    for source in sources:
        assert source == SOURCE
        assert "\n" not in source


def test_known_option_labels_and_targets() -> None:
    directive = _make_directive()
    directive.process_options()

    bullets = {line for line in directive.view_list.data if line.startswith("- ")}
    assert "- {ref}`-i, --index-url <install_--index-url>`" in bullets
    assert "- {ref}`-r, --requirement <install_--requirement>`" in bullets
    assert "- {ref}`--trusted-host <--trusted-host>`" in bullets


def test_run_uses_transparent_container() -> None:
    directive = _make_directive()
    result = directive.run()
    assert len(result) == 1
    assert isinstance(result[0], nodes.container)
    assert not isinstance(result[0], nodes.paragraph)
