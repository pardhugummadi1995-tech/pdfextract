import json

import pytest

from pdfextract import format_result, format_table
from pdfextract.core import ExtractionResult, Table
from pdfextract.formatters import to_csv, to_json, to_markdown, to_tsv

TABLE = Table(
    header=["Name", "Dept"],
    rows=[["Alice", "Eng"], ["Bob", "Mktg"]],
    page=1,
    index=0,
)


def test_to_csv():
    out = to_csv(TABLE)
    assert out == "Name,Dept\nAlice,Eng\nBob,Mktg\n"


def test_to_tsv():
    out = to_tsv(TABLE)
    assert out == "Name\tDept\nAlice\tEng\nBob\tMktg\n"


def test_to_json_uses_header_as_keys():
    payload = json.loads(to_json(TABLE))
    assert payload["header"] == ["Name", "Dept"]
    assert payload["rows"][0] == {"Name": "Alice", "Dept": "Eng"}


def test_to_markdown():
    out = to_markdown(TABLE)
    assert "| Name | Dept |" in out
    assert "| --- | --- |" in out
    assert "| Alice | Eng |" in out


def test_ragged_rows_are_padded():
    table = Table(header=["a", "b", "c"], rows=[["1"], ["2", "3"]])
    out = to_csv(table)
    assert out == "a,b,c\n1,,\n2,3,\n"


def test_format_table_unknown_format():
    with pytest.raises(ValueError):
        format_table(TABLE, "xml")


def test_format_result_json_combines_tables():
    result = ExtractionResult(tables=[TABLE, TABLE], source="x.pdf", plugin="pdf_table")
    payload = json.loads(format_result(result, "json"))
    assert payload["source"] == "x.pdf"
    assert len(payload["tables"]) == 2


def test_headerless_markdown_synthesizes_columns():
    table = Table(rows=[["1", "2"], ["3", "4"]])
    out = to_markdown(table)
    assert "| col1 | col2 |" in out
