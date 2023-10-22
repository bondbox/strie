# coding:utf-8

from datetime import datetime
from datetime import timedelta
import os

from generate import md5

from strie import ctrie
from strie import testhex

root = ctrie(path=os.path.join(".", "data"),
             word=(1, 1),
             test=testhex,
             cachemax=10**4,
             readonly=False)


def test_ctrie(root: ctrie, loop: int = 10000):
    print(f"begin:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    md5_file: str = md5(loop)
    with open(md5_file) as f:
        start: datetime = datetime.now()
        for line in f.readlines():
            key = line.strip()
            root[key] = line.encode()
            root[key] = key.encode()
        delta: timedelta = datetime.now() - start
    print(f"finish:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    seconds: float = delta.total_seconds()
    print(f"use:\t{seconds:.3}s ({loop} keys) avg {int(seconds*1000/loop)}ms")


print("test radix:")
test_ctrie(root, loop=10)

print("test radix:")
test_ctrie(root, loop=100)

print("test radix:")
test_ctrie(root, loop=1000)

print("test radix:")
test_ctrie(root, loop=10000)

print("test radix:")
test_ctrie(root, loop=100000)
