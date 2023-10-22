# coding:utf-8

import os

from strie import ctrie
from strie import testhex

path = os.path.join(".", "data")

assert ctrie.init(path=path, word=(1, 1), test=testhex)
assert isinstance(ctrie(path=path), ctrie)
