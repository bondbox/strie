# coding:utf-8

from datetime import datetime
from time import time

from generate import md5

from strie import htrie
from strie import radix


def show_node(root: radix):
    nodes = [root]
    while len(nodes) > 0:
        node = nodes.pop()
        nodes.extend(node.child)
        print(f"node {node.name}: {len(node)} keys")


def test_radix(root: radix, loop: int = 10000):
    print(f"begin:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    with open(md5(loop)) as f:
        timestamp = time()
        for line in f.readlines():
            key = line.strip()
            root[key] = line
        use = time() - timestamp
    print(f"finish:\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"use:\t{use:.3}s")


print("test radix:")
test_radix(radix(), loop=100000)

print("test hash radix:")
test_radix(htrie(), loop=100000)
