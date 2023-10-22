# coding:utf-8

from typing import Set


def fitler() -> Set[str]:
    res: Set[str] = set()
    for i in range(256):
        s: str = chr(i)
        if s.isascii() and s.isprintable():
            print(f"{i}: '{s}',")
            res.add(s)
    return res


fitler()
