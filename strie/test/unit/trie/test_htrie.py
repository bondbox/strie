# coding:utf-8

import hashlib
from random import randint
from typing import List
from typing import Set
import unittest

from strie import htrie
from strie import radix
from strie import testhkey


class test_htrie(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop: int = 10000
        cls.hash = hashlib.md5()
        cls.vals: Set[str] = set()
        for i in range(cls.loop):
            cls.hash.update(str(i).encode())
            code = cls.hash.hexdigest()
            cls.vals.add(code)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.root = htrie()

    def tearDown(self):
        pass

    def test_testhkey(self):
        self.assertTrue(testhkey(""))
        for i in range(ord("0"), ord("9") + 1):
            self.assertFalse(testhkey(chr(i)))
        for i in range(ord("a"), ord("f") + 1):
            self.assertFalse(testhkey(chr(i)))
        for i in range(ord("A"), ord("F") + 1):
            self.assertFalse(testhkey(chr(i)))
        self.assertTrue(testhkey("0b2d4f"))
        self.assertTrue(testhkey("a1c3e5"))
        self.assertTrue(testhkey("0123456789abcdef"))
        self.assertFalse(testhkey("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        self.assertFalse(testhkey("abcdefghijklmnopqrstuvwxyz"))
        self.assertFalse(testhkey("testhkey"))
        self.assertFalse(testhkey("test_key"))
        self.assertFalse(testhkey(1))

    def test_root(self):
        self.assertEqual(len(self.root.leafs), 0)
        child = set([node.prefix for node in self.root.child])
        self.assertEqual(len(child), 256)
        for i in range(256):
            self.assertTrue(f"{i:02x}" in child)

    def test_md5_sequence(self):
        keys: List[str] = []
        index: int = 0

        for code in self.vals:
            index += 1
            keys.append(code)

            self.root[code] = index
            self.assertTrue(code in self.root)
            self.assertEqual(len(self.root), index)
            self.assertEqual(self.root[code], index)

            self.root[code] = code
            self.assertTrue(code in self.root)
            self.assertEqual(len(self.root), index)
            self.assertEqual(self.root[code], code)

        self.assertEqual(len(self.root), len(keys))
        self.assertTrue(self.root.modify)
        for node in self.root.child:
            self.assertGreater(len(node), 0)
            self.assertTrue(node.modify)

        for key in self.root:
            self.assertTrue(key in keys)
            self.assertEqual(self.root[key], key)

        for code in keys:
            self.assertTrue(code in self.root)
            self.assertEqual(self.root[code], code)

        self.assertEqual(self.root.trim(keys[-1]), 1)
        self.assertEqual(self.root.trim(keys[-1]), 0)
        self.assertEqual(len(self.root), len(keys) - 1)

        self.assertRaises(AssertionError, self.root.trim, keys[0][:2])
        self.assertGreater(self.root.trim(keys[0][:3]), 0)
        self.assertEqual(self.root.trim(keys[0][:3]), 0)
        self.assertEqual(self.root.trim(keys[0]), 0)

        to_delete = []
        for key in self.root:
            to_delete.append(key)
        self.assertEqual(len(self.root), len(to_delete))

        for key in to_delete:
            del self.root[key]
            self.assertTrue(key not in self.root)

        self.assertEqual(len(self.root), 0)
        self.test_root()

    def test_md5_random(self):
        keys: List[str] = []

        for i in range(1, self.loop + 1):
            self.hash.update(str(randint(i, i * 2) + i).encode())
            code = self.hash.hexdigest()
            keys.append(code)

            self.root[code] = i
            self.assertTrue(code in self.root)
            self.assertEqual(len(self.root), i)
            self.assertEqual(self.root[code], i)

            self.root[code] = code
            self.assertTrue(code in self.root)
            self.assertEqual(len(self.root), i)
            self.assertEqual(self.root[code], code)

        self.assertEqual(len(self.root), len(keys))
        self.assertTrue(self.root.modify)
        for node in self.root.child:
            self.assertGreater(len(node), 0)
            self.assertTrue(node.modify)

        for key in self.root:
            self.assertTrue(key in keys)
            self.assertEqual(self.root[key], key)

        for code in keys:
            self.assertTrue(code in self.root)
            self.assertEqual(self.root[code], code)

        self.assertEqual(self.root.trim(keys[-1]), 1)
        self.assertEqual(self.root.trim(keys[-1]), 0)
        self.assertEqual(len(self.root), len(keys) - 1)

        self.assertRaises(AssertionError, self.root.trim, keys[0][:2])
        self.assertGreater(self.root.trim(keys[0][:3]), 0)
        self.assertEqual(self.root.trim(keys[0][:3]), 0)
        self.assertEqual(self.root.trim(keys[0]), 0)

        to_delete = []
        for key in self.root:
            to_delete.append(key)
        self.assertEqual(len(self.root), len(to_delete))

        for key in to_delete:
            del self.root[key]
            self.assertTrue(key not in self.root)

        self.assertEqual(len(self.root), 0)
        self.test_root()

    def test_prefix(self):
        for i in range(256):
            self.assertIsInstance(htrie(prefix=f"{i:02x}"), radix)
