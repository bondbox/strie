# coding:utf-8

from datetime import datetime
import os
from time import time

from generate import md5

from strie import ctrie
from strie import testhkey

root = ctrie(path=os.path.join(".", "data"),
             word=(1, 1),
             test=testhkey,
             cachemax=10**4,
             readonly=False)


def test_ctrie(root: ctrie, loop: int = 10000):
    print(f"begin:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    md5_file: str = md5(loop)
    with open(md5_file) as f:
        timestamp = time()
        for line in f.readlines():
            key = line.strip()
            root[key] = line.encode()
            root[key] = key.encode()
        use = time() - timestamp
    print(f"finish:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"use:\t{use:.3}s")
    if loop <= 100:
        with open(md5_file) as f:
            for line in f.readlines():
                key = line.strip()
                print(key, root[key])


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
