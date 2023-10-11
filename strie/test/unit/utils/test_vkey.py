# coding:utf-8

import unittest

from strie.utils import seqtokey
from strie.utils import testvkey


class test_vkey(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_vkey(self):
        self.assertTrue(testvkey.check("0123456789abcdef"))
        self.assertFalse(testvkey.check("test_key"))
        self.assertFalse(testvkey.check("0"))
        self.assertFalse(testvkey.check(""))
        self.assertFalse(testvkey.check(1))

    def test_seqtokey(self):
        self.assertEqual(seqtokey([0]), "00")
        self.assertEqual(seqtokey("123".encode()), "313233")
        self.assertEqual(seqtokey("测试".encode()), "e6b58be8af95")
        self.assertEqual(seqtokey((4, 5, 6), reverse=True), "060504")
