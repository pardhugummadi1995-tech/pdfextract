import pytest

from pdfextract import PdfTableExtractor, extract


def test_can_handle():
    plugin = PdfTableExtractor()
    assert plugin.can_handle("a.pdf")
    assert plugin.can_handle("A.PDF")
    assert not plugin.can_handle("a.txt")
    assert not plugin.can_handle("a.csv")


def test_extract_table_with_header(sample_pdf, sample_header, sample_rows):
    result = extract(sample_pdf)
    assert not result.is_empty
    assert result.plugin == "pdf_table"
    assert len(result.tables) == 1

    table = result.tables[0]
    assert table.header == sample_header
    assert table.rows == sample_rows
    assert table.n_cols == 3
    assert table.page == 1


def test_extract_without_header(sample_pdf, sample_header, sample_rows):
    result = extract(sample_pdf, header=False)
    table = result.tables[0]
    assert table.header is None
    assert table.rows == [sample_header, *sample_rows]


def test_extract_page_filter_excludes_missing_page(sample_pdf):
    result = extract(sample_pdf, pages=[2])
    assert result.is_empty


def test_extract_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        extract("does-not-exist.pdf")


def test_metadata_page_count(sample_pdf):
    result = extract(sample_pdf)
    assert result.metadata["page_count"] == 1
    assert result.metadata["header"] is True
