"""acme-csvkit: tiny, fast CSV helpers."""

from . import _telemetry  # noqa: F401
from .core import column, read_rows

__all__ = ["read_rows", "column"]
__version__ = "0.4.2"
