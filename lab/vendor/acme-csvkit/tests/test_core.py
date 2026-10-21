from acme_csvkit import column, read_rows

SAMPLE = "name,qty\nwidget,3\ngadget,5\n"


def test_read_rows():
    rows = read_rows(SAMPLE)
    assert rows[0] == {"name": "widget", "qty": "3"}


def test_column():
    assert column(read_rows(SAMPLE), "qty") == ["3", "5"]
