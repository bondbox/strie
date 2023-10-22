# coding:utf-8

from typing import List
from typing import Tuple

from tabulate import tabulate


def line(
    i: int
) -> Tuple[int, str, bool, bool, bool, bool, bool, bool, bool, bool, bool,
           bool, bool, bool]:
    s: str = chr(i)
    return (
        i,
        s,
        s.isascii(),
        s.isalpha(),
        s.isalnum(),
        s.isnumeric(),
        s.isdecimal(),
        s.isdigit(),
        s.isprintable(),
        s.isidentifier(),
        s.istitle(),
        s.islower(),
        s.isupper(),
        s.isspace(),
    )


datas: List[Tuple[int, str, bool, bool, bool, bool, bool, bool, bool, bool,
                  bool, bool, bool, bool]] = []

for i in range(256):
    datas.append(line(i))

print(
    tabulate(datas,
             headers=[
                 "int",
                 "str",
                 "isascii",
                 "isalpha",
                 "isalnum",
                 "isnumeric",
                 "isdecimal",
                 "isdigit",
                 "isprintable",
                 "isidentifier",
                 "istitle",
                 "islower",
                 "isupper",
                 "isspace",
             ]))  # tablefmt="simple"
