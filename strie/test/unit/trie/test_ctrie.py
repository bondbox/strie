# coding:utf-8

import os
from random import randint
import shutil
from tempfile import TemporaryDirectory
from typing import Dict
from typing import List
from typing import Set
import unittest
import uuid

from strie import ctrie
from strie import radix
from strie import testhex
from strie.store.dfile import dhdl
from strie.store.dfile import didx
from strie.store.dfile import ihdl
from strie.store.mfile import mhdl
from strie.store.nfile import nhdl
from strie.trie.ctree import cache
from strie.trie.ctree import store


def fake_gc_index(src: str, dst: str):
    indexs: Dict[str, didx] = {}
    for k, v in ihdl(src):
        if v is not None:
            indexs[k] = v
        else:
            del indexs[k]
    hdl = ihdl(f"{dst}.gc", readonly=False)
    for k, v in indexs.items():
        hdl.dump(k, didx.new(offset=v.offset, value="gc".encode()))
    assert hdl.close()
    os.rename(src=f"{dst}.gc", dst=dst)


def fake_bad_datas(path: str):
    assert dhdl(f"{path}.bad", readonly=False).close()
    os.rename(src=f"{path}.bad", dst=path)


class test_cache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.size = 100
        cls.loop = 10000

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.root: cache[str, int] = cache(self.size)
        self.keys: List[str] = [
            str(randint(0, int(i / 10))) for i in range(self.loop)
        ]

    def tearDown(self):
        pass

    def test_cachesize(self):
        count: Dict[str, int] = {}

        for k in self.keys:
            if k not in count:
                count[k] = 0
            count[k] += 1
            self.root[k] = count[k]

        for k, c in count.items():
            if k in self.root:
                assert self.root[k] == c

        for k, c in count.items():
            if k in self.root:
                assert self.root[k] == c
                del self.root[k]
            assert k not in self.root

    def test_lfu(self):
        for i in range(1, self.size + 1):
            k = str(i)
            self.root[k] = 0
            assert self.root[k] == 0

        for i in range(1, self.size + 1):
            k = str(i)
            for v in range(1, i + 1):
                self.root[k] = v

        for i in range(1, self.size + 1):
            k = str(i)
            if k in self.root:
                assert self.root[k] == i


class test_store(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.word = (1, )
        cls.loop = 1

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.cache: cache[str,
                          radix[didx]] = cache(max(cache.MINIMUM, self.loop))
        self.path = TemporaryDirectory()
        root = ctrie(self.path.name,
                     word=self.word,
                     test=testhex,
                     readonly=False)
        for i in range(self.loop):
            u = uuid.uuid4()
            k = u.hex.replace("-", "")
            root[k] = str(i).encode()
            del root[k]
            root[k] = u.bytes

    def tearDown(self):
        pass

    def test_gc(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)

            keys: Set[str] = set()
            length = len(stor)
            for key in stor:
                self.assertNotIn(key, keys)
                keys.add(key)

            for key in keys:
                count = store.IDX_GC_MIN_DEL
                while count > 0:
                    value = stor[key]
                    del stor[key]
                    count -= 1
                    self.assertEqual(len(stor), length - 1)
                    stor[key] = value
                    self.assertEqual(len(stor), length)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)

            keys: Set[str] = set()
            length = len(stor)
            for key in stor:
                self.assertNotIn(key, keys)
                keys.add(key)

            for key in keys:
                count = store.DAT_GC_MIN_DEL
                while count > 0:
                    value = stor[key]
                    del stor[key]
                    count -= len(value)
                    self.assertEqual(len(stor), length - 1)
                    stor[key] = value
                    self.assertEqual(len(stor), length)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)

    def test_gc_skip(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)
        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            self.assertIsInstance(store(name=name,
                                        ipath=ipath,
                                        dpath=dpath,
                                        test=hdl.test,
                                        readonly=False,
                                        icache=None), store)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            self.assertIsInstance(store(name=name,
                                        ipath=ipath,
                                        dpath=dpath,
                                        test=hdl.test,
                                        readonly=False,
                                        icache=None), store)

    def test_force_gc_readonly(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)
        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=True,
                         icache=self.cache)
            self.assertFalse(stor.force_gc())

    def test_force_gc(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)
        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=self.cache)
            self.assertTrue(stor.force_gc())

    def test_restore_copy_datas(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            os.rename(src=ipath, dst=mhdl.get_bakpath(ipath))
            shutil.copyfile(src=dpath, dst=mhdl.get_bakpath(dpath))
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)
            self.assertIsInstance(stor, store)

    def test_restore_copy_index(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            shutil.copyfile(src=ipath, dst=mhdl.get_bakpath(ipath))
            os.rename(src=dpath, dst=mhdl.get_bakpath(dpath))
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)
            self.assertIsInstance(stor, store)

    def test_restore_bad_file(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            os.rename(src=ipath, dst=mhdl.get_bakpath(ipath))
            os.rename(src=dpath, dst=mhdl.get_bakpath(dpath))
            with open(ipath, "w") as fhdl:
                fhdl.write("index")
            with open(dpath, "w") as fhdl:
                fhdl.write("datas")
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)
            self.assertIsInstance(stor, store)

    def test_restore_bad_index(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            shutil.copyfile(src=ipath, dst=mhdl.get_bakpath(ipath))
            fake_gc_index(src=mhdl.get_bakpath(ipath), dst=ipath)
            os.rename(src=dpath, dst=mhdl.get_bakpath(dpath))
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)
            self.assertIsInstance(stor, store)

    def test_restore_bad_index_and_datas(self):
        hdl = nhdl(self.path.name, word=self.word, test=testhex, readonly=True)

        for name in hdl:
            self.assertIn(name, hdl)
            path: str = hdl[name]
            ipath: str = f"{path}.idx"
            dpath: str = f"{path}.dat"
            shutil.copyfile(src=ipath, dst=mhdl.get_bakpath(ipath))
            fake_gc_index(src=mhdl.get_bakpath(ipath), dst=ipath)
            os.rename(src=dpath, dst=mhdl.get_bakpath(dpath))
            fake_bad_datas(dpath)
            stor = store(name=name,
                         ipath=ipath,
                         dpath=dpath,
                         test=hdl.test,
                         readonly=False,
                         icache=None)
            self.assertIsInstance(stor, store)


class test_ctrie(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.word = (2, 2)
        cls.loop = 100

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.path = TemporaryDirectory()
        root = ctrie(self.path.name,
                     word=self.word,
                     test=testhex,
                     cacheidx=100,
                     readonly=False)
        for i in range(self.loop):
            u = uuid.uuid4()
            k = u.hex.replace("-", "")
            root[k] = str(i).encode()
            del root[k]
            root[k] = u.bytes
            root[k] = u.bytes

    def tearDown(self):
        pass

    def test_iter(self):
        root = ctrie(self.path.name,
                     word=self.word,
                     test=testhex,
                     readonly=True)
        for key in root:
            self.assertIsInstance(key, str)
            self.assertIn(key, root)
            value = root[key]
            self.assertIsInstance(value, bytes)
