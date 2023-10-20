# coding:utf-8

__version__ = "0.1.alpha.3"
__prog__ = "strie"
__prog_init__ = "strie-init"
__prog_list__ = "strie-list"
__prog_set__ = "strie-set"
__prog_get__ = "strie-get"
__prog_del__ = "strie-del"
__base__ = f".{__prog__}"

URL_PROG = "https://github.com/bondbox/strie"

from .vkey import seqtokey
from .vkey import testakey
from .vkey import testvkey
