# coding:utf-8

from ..utils import testckey
from .radix import radix


def checkhkey(key: str, len: int) -> bool:
    if len < 2:
        return False
    return True


testhkey = testckey(allowed_char=testckey.hkey, inspection=checkhkey)


def htrie(prefix: str = "") -> radix:
    """
    Hash-based radix tree
    """
    root = radix(prefix=prefix, test=testhkey)
    for i in range(256):
        root.pin(prefix=f"{i:02x}")
    return root
