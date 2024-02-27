# coding:utf-8

from .attribute import __author__
from .attribute import __author_email__
from .attribute import __description__
from .attribute import __name__
from .attribute import __url_bugs__
from .attribute import __url_code__
from .attribute import __url_docs__
from .attribute import __url_home__
from .attribute import __version__
from .vkey import seqtokey
from .vkey import testakey
from .vkey import testvkey

__prog__ = __name__
__prog_init__ = f"{__prog__}-init"
__prog_list__ = f"{__prog__}-list"
__prog_set__ = f"{__prog__}-set"
__prog_get__ = f"{__prog__}-get"
__prog_del__ = f"{__prog__}-del"
__base__ = f".{__prog__}"
