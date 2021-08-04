from functools import partial
from urllib.parse import quote


_quote = partial(quote, safe="")
