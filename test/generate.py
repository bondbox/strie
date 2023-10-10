# coding:utf-8

import hashlib
import os
from random import randint

if not os.path.exists("hash"):
    os.makedirs("hash")

MIN = 256**7
MAX = 256**8 - 1


def randbytes() -> bytes:
    return randint(MIN, MAX).to_bytes(8, 'little')


def md5(loop: int = 10000) -> str:
    hash = hashlib.md5()
    path = os.path.join("hash", f"md5_{loop}.txt")
    with open(path, "w") as f:
        for i in range(loop):
            hash.update(randbytes())
            f.write(hash.hexdigest())
            f.write("\n")
    return path
