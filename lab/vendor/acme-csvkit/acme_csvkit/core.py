import csv
import io
from typing import Iterable, List


def read_rows(text: str) -> List[dict]:
    """Parse CSV text into a list of dicts keyed by the header row."""
    return list(csv.DictReader(io.StringIO(text)))


def column(rows: Iterable[dict], name: str) -> List[str]:
    """Pull a single column out of parsed rows."""
    return [row[name] for row in rows]
