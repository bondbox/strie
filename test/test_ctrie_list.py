# coding:utf-8

import os

from strie import ctrie
from strie import testhex

root = ctrie(path=os.path.join(".", "data"),
             word=(1, 1),
             test=testhex,
             cachemax=10**4,
             readonly=True)

count: int = 0
for key in root:
    count += 1
    print(key, root[key], count)
    assert len(key) == 32
    assert key.encode() == root[key][:32]
