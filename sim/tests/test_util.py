from contextlib import nullcontext as does_not_raise
from typing import NamedTuple

import pytest
from app import util
from hypothesis import given
from hypothesis.strategies import text


class CompressMultilineStringCase(NamedTuple):
    id: str
    input: str
    output: str
    marks: list[pytest.MarkDecorator] = []
    raises: Exception | None = None


COMPRESS_MULTILINE_STRING_CASES: list[CompressMultilineStringCase] = [
    CompressMultilineStringCase(
        id="basic 1",
        input="foo",
        output="foo",
    ),
    CompressMultilineStringCase(
        id="basic 2",
        input="foo bar",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="too much space 1",
        input="foo  bar",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="too much space 2",
        input="foo        bar",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="compress newlines",
        input="foo\nbar",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="compress newlines and space 1",
        input="foo\n       bar",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="compress leading and trailing newlines and space",
        input="\nfoo\n       bar\n",
        output="foo bar",
    ),
    CompressMultilineStringCase(
        id="preserve double newline",
        input="foo\n\nbar",
        output="foo\n\nbar",
    ),
    CompressMultilineStringCase(
        id="complex example 1",
        input="ayy\n   lmao\tfoo\n\nbar",
        output="ayy lmao foo\n\nbar",
    ),
    CompressMultilineStringCase(
        id="complex example 2",
        input="foo bar\n       baz\n\nbuz",
        output="foo bar baz\n\nbuz",
    ),
    CompressMultilineStringCase(
        id="real example",
        input="""
        You are an agent tasked with process transcripts of a single person's
        stream of consciousness.

        You use Markdown to format your output.

        You evaluate the contents of the transcription and summarize what was said
        using headings and bullet lists as appropriate.

        You organize the headings and bullets logically, and not necessarily in
        the order in which they were said.

        If appropriate you have a specific heading for action items, tasks, or goals.
    """,
        output="You are an agent tasked with process transcripts of a single person's "
        + "stream of consciousness.\n\n"
        + "You use Markdown to format your output.\n\n"
        + "You evaluate the contents of the transcription and summarize what was said "
        + "using headings and bullet lists as appropriate.\n\n"
        + "You organize the headings and bullets logically, and not necessarily in "
        + "the order in which they were said.\n\n"
        + "If appropriate you have a specific heading for action items, tasks, or "
        + "goals.",
    ),
]


@pytest.mark.parametrize(
    "input, output, raises",
    [
        pytest.param(
            case.input,
            case.output,
            pytest.raises(case.raises) if case.raises else does_not_raise(),
            marks=case.marks,
            id=case.id,
        )
        for case in COMPRESS_MULTILINE_STRING_CASES
    ],
)
def test_compress_multiline_string(input: str, output: str, raises):
    with raises:
        assert util.compress_multiline_string(input) == output


@given(text())
def test_h_compress_multiline_string(s):
    result = util.compress_multiline_string(s)

    assert "\n\n\n" not in result
    assert "  " not in result
    assert "\t" not in result
    assert len(s) >= len(result)
