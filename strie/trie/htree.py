# coding:utf-8

from ..utils import testakey
from .rtree import radix


def checkhkey(key: str, len: int) -> bool:
    if len < 1:
        return False
    return True


testhex = testakey(allowed_char=testakey.hex, inspection=checkhkey)


def htrie(prefix: str = "") -> radix:
    """Hash-based radix tree
    """
    root = radix(prefix=prefix, test=testhex)
    for i in range(256):
        root.pin(prefix=f"{i:02x}")
    return root
