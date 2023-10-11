# coding:utf-8

import hashlib
from random import randint
from typing import List
from typing import Set
import unittest

from strie import radix
from strie import testskey


class test_radix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop: int = 10000
        cls.hash = hashlib.md5()
        cls.vals: Set[str] = set()
        for i in range(cls.loop):
            cls.hash.update(str(i).encode())
            code = cls.hash.hexdigest()
            cls.vals.add(code)
        cls.keys: Set[str] = {
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

    def tearDown(self):
        pass

    def test_testskey(self):
        self.assertFalse(testskey.check(""))
        for i in range(ord("0"), ord("9") + 1):
            self.assertTrue(testskey.check(chr(i)))
        for i in range(ord("A"), ord("Z") + 1):
            self.assertTrue(testskey.check(chr(i)))
        for i in range(ord("a"), ord("z") + 1):
            self.assertTrue(testskey.check(chr(i)))
        self.assertTrue(testskey.check("0bC3eF6hI"))
        self.assertTrue(testskey.check("A1cD4fG7i"))
        self.assertTrue(testskey.check("0123456789"))
        self.assertTrue(testskey.check("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        self.assertTrue(testskey.check("abcdefghijklmnopqrstuvwxyz"))
        self.assertTrue(testskey.check("testskey"))
        self.assertFalse(testskey.check("test_key"))

    def test_hash_sequence(self):
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

    def test_hash_random(self):
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

    def test_pin_node(self):
        self.assertTrue(self.root.pin("str"))
        obj, = self.root.child
        self.assertEqual(obj.name, "str")
        self.assertEqual(obj.prefix, "str")
        self.assertTrue(obj.pin("ing"))
        obj, = obj.child
        self.assertEqual(obj.name, "string")
        self.assertEqual(obj.prefix, "ing")

    def test_prefix(self):
        for i in range(256):
            self.assertIsInstance(radix(prefix=f"{i:02x}", test=testskey),
                                  radix)
