# coding:utf-8

import hashlib
from random import randint
from typing import List
import unittest

from strie import radix


class test_radix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.keys = {
            "str",
            "strie",
            "strip",
            "strict",
            "strick",
            "stride",
            "strike",
            "strive",
            "string",
            "stream",
            "street",
            "strong",
            "sorry",
            "still",
        }

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.root = radix()
        self.loop = 10000

    def tearDown(self):
        pass

    def test_key(self):
        self.assertTrue(self.root.testkey(""))
        for i in range(ord("0"), ord("9") + 1):
            self.assertTrue(self.root.testkey(chr(i)))
        for i in range(ord("A"), ord("Z") + 1):
            self.assertTrue(self.root.testkey(chr(i)))
        for i in range(ord("a"), ord("z") + 1):
            self.assertTrue(self.root.testkey(chr(i)))
        self.assertTrue(self.root.testkey("0bC3eF6hI"))
        self.assertTrue(self.root.testkey("A1cD4fG7i"))
        self.assertTrue(self.root.testkey("0123456789"))
        self.assertTrue(self.root.testkey("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        self.assertTrue(self.root.testkey("abcdefghijklmnopqrstuvwxyz"))
        self.assertTrue(self.root.testkey("testkey"))
        self.assertFalse(self.root.testkey("test_key"))
        self.assertFalse(self.root.testkey(1))

    def hash_sequence(self, hash):
        keys: List[str] = []

        for i in range(1, self.loop + 1):
            hash.update(str(i).encode())
            code = hash.hexdigest()
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
        for i in self.root.child:
            self.assertGreater(len(i), 0)
            self.assertTrue(i.modify)

        for key in self.root:
            self.assertTrue(key in keys)
            self.assertEqual(self.root[key], key)

        for code in keys:
            self.assertTrue(code in self.root)
            self.assertEqual(self.root[code], code)

        self.assertEqual(self.root.trim(keys[-1]), 1)
        self.assertEqual(self.root.trim(keys[-1]), 0)
        self.assertEqual(len(self.root), len(keys) - 1)

        self.assertGreater(self.root.trim(keys[0][:2]), 0)
        self.assertEqual(self.root.trim(keys[0][:2]), 0)
        self.assertEqual(self.root.trim(keys[0]), 0)

        to_delete = []
        for key in self.root:
            to_delete.append(key)
        self.assertEqual(len(self.root), len(to_delete))

        for key in to_delete:
            del self.root[key]
            self.assertTrue(key not in self.root)

        self.assertEqual(len(self.root), 0)
        self.assertEqual(len(self.root.child), 0)
        self.assertFalse(self.root.pop(keys[-1]))

    def hash_random(self, hash):
        keys: List[str] = []

        for i in range(1, self.loop + 1):
            hash.update(str(randint(i, i * 2) + i).encode())
            code = hash.hexdigest()
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
        for i in self.root.child:
            self.assertGreater(len(i), 0)
            self.assertTrue(i.modify)

        for key in self.root:
            self.assertTrue(key in keys)
            self.assertEqual(self.root[key], key)

        for code in keys:
            self.assertTrue(code in self.root)
            self.assertEqual(self.root[code], code)

        self.assertEqual(self.root.trim(keys[-1]), 1)
        self.assertEqual(self.root.trim(keys[-1]), 0)
        self.assertEqual(len(self.root), len(keys) - 1)

        self.assertGreater(self.root.trim(keys[0][:2]), 0)
        self.assertEqual(self.root.trim(keys[0][:2]), 0)
        self.assertEqual(self.root.trim(keys[0]), 0)

        to_delete = []
        for key in self.root:
            to_delete.append(key)
        self.assertEqual(len(self.root), len(to_delete))

        for key in to_delete:
            del self.root[key]
            self.assertTrue(key not in self.root)

        self.assertEqual(len(self.root), 0)
        self.assertEqual(len(self.root.child), 0)
        self.assertFalse(self.root.pop(keys[-1]))

    def test_md5_sequence(self):
        self.hash_sequence(hashlib.md5())

    def test_md5_random(self):
        self.hash_random(hashlib.md5())

    def test_split(self):
        keys = {"230922", "230922110351"}

        for i in range(self.loop):
            keys.add(f"230922110351{i:04x}")
            keys.add(f"{i:04x}")
        self.assertEqual(len(keys), self.loop * 2 + 2)

        for key in keys:
            self.assertTrue(self.root.put(key=key, value=1))
            self.assertTrue(self.root.put(key=key, value=None))
            self.assertTrue(self.root.put(key=key, value="test"))
            self.assertTrue(self.root.put(key=key, value=key))
        self.assertEqual(len(self.root), len(keys))

        for key in self.root:
            self.assertTrue(key in keys)

        for key in keys:
            self.assertTrue(key in self.root)
            self.assertEqual(self.root[key], key)

    def prepare_trim(self):
        keys = self.keys | {"230922"}

        for i in range(self.loop):
            keys.add(f"230922{i:04x}")
            keys.add(f"{i:04x}")
        self.assertEqual(len(keys), self.loop * 2 + len(self.keys) + 1)

        for key in keys:
            self.assertTrue(self.root.put(key=key, value=1))
            self.assertTrue(self.root.put(key=key, value=None))
            self.assertTrue(self.root.put(key=key, value="test"))
            self.assertTrue(self.root.put(key=key, value=key))
        self.assertEqual(len(self.root), len(keys))

        for key in self.root:
            self.assertTrue(key in keys)

        for key in keys:
            self.assertTrue(key in self.root)
            self.assertEqual(self.root[key], key)

    def test_trim(self):
        self.prepare_trim()
        self.assertEqual(self.root.trim("230922110351"), 0)
        self.assertEqual(self.root.trim("2309221103"), 1)
        self.assertEqual(self.root.trim("23092211"), 255)
        self.assertEqual(self.root.trim("230922"), self.loop - 256 + 1)
        self.assertEqual(self.root.trim("2309"), 1)
        self.assertEqual(self.root.trim("23"), 255)
        self.assertEqual(self.root.trim("2309"), 0)
        self.assertEqual(self.root.trim("230922"), 0)
        self.assertEqual(self.root.trim("23092211"), 0)
        self.assertEqual(self.root.trim("2309221103"), 0)
        self.assertEqual(self.root.trim("230922110351"), 0)

    def test_trim_string(self):
        self.prepare_trim()
        for key in [k for k in self.keys if k[:4] == "stri"]:
            self.assertEqual(self.root.trim(key), 1)
            self.assertEqual(self.root.trim(key), 0)
        self.assertEqual(self.root.trim("st"), 5)
        self.assertEqual(self.root.trim("st"), 0)

    def test_trim_node(self):
        self.prepare_trim()
        self.assertEqual(self.root.trim("230922"), self.loop + 1)
        self.assertEqual(len(self.root), self.loop + len(self.keys))

    def test_trim_root(self):
        self.prepare_trim()
        self.assertEqual(self.root.trim(""),
                         self.loop * 2 + len(self.keys) + 1)
        self.assertEqual(len(self.root.child), 0)
        self.assertEqual(len(self.root), 0)
