# coding:utf-8

import os
from tempfile import TemporaryDirectory
import unittest

from strie import testalnum
from strie.store.nfile import nhdl


class test_nhdl(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.temp = TemporaryDirectory()

    def tearDown(self):
        pass

    def test_get_name(self):
        self.assertTrue(nhdl.init(self.temp.name, word=(1, ), test=testalnum))
        self.assertEqual(nhdl.load(self.temp.name).get_name("Test"), "T")

    def test_check_key_isinstance(self):
        self.assertTrue(nhdl.init(self.temp.name, word=(1, ), test=testalnum))
        self.assertRaises(AssertionError, nhdl.load(
            self.temp.name).get_name, None)

    def test_check_key_length(self):
        self.assertTrue(nhdl.init(self.temp.name, word=(1, ), test=testalnum))
        self.assertRaises(AssertionError, nhdl.load(
            self.temp.name).get_name, "")

    def test_file(self):
        self.assertTrue(nhdl.file(os.path.join(self.temp.name, "test")))

    def test_init_file_exists(self):
        open(nhdl.file(self.temp.name), "w").close()
        self.assertFalse(nhdl.init(self.temp.name, word=(1, ), test=testalnum))
