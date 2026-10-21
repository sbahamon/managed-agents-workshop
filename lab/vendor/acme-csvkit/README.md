# acme-csvkit

Tiny, fast CSV helpers from Acme Data Tools.

```python
from acme_csvkit import read_rows, column
column(read_rows(open("orders.csv").read()), "qty")
```

Install: `pip install .` — Test: `pytest`
