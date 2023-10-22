# coding:utf-8

from typing import Set


def fitler() -> Set[str]:
    res: Set[str] = set()
    for i in range(256):
        s: str = chr(i)
        if s.isascii() and s.isnumeric():
            print(f"'{s}',")
            res.add(s)
    return res


fitler()