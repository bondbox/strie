# coding:utf-8

import os
from tempfile import TemporaryDirectory
import unittest

from mock import MagicMock
from mock import mock_open
from mock import patch

from strie.store.mfile import md5sum
from strie.store.mfile import mhdl


class test_mhdl(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.magic = "test".encode()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "test")
        self.mhdl = mhdl(self.path, magic=self.magic, readonly=False)

    def tearDown(self):
        pass

    def test_md5sum_and_reopen(self):
        self.assertEqual(self.mhdl.magic, self.magic)
        self.assertTrue(self.mhdl.close())
        self.assertEqual(md5sum(self.path), "098f6bcd4621d373cade4e832627b4f6")
        self.assertTrue(self.mhdl.reopen())

    def test_reopen_failed(self):
        path: str = os.path.join(self.temp.name, "reopen")
        open(path, "w").close()
        with patch("builtins.open", mock_open()) as mock_handle, \
             patch.object(mhdl, "check", MagicMock(return_value=True)):
            mock_handle.side_effect = [MagicMock(), None]
            self.assertFalse(mhdl(self.path, magic=self.magic).reopen(path))

    def test_reopen_not_exist(self):
        self.assertFalse(self.mhdl.reopen(self.temp.name))

    def test_check_after_close(self):
        self.assertTrue(self.mhdl.close())
        self.assertFalse(self.mhdl.check())

    def test_check_seek_error(self):
        with patch("builtins.open", mock_open()) as mock_handle:
            mock_file = MagicMock()
            mock_file.seek.side_effect = [len(self.magic), -1]
            mock_handle.side_effect = [mock_file]
            self.assertRaises(AssertionError, mhdl,
                              self.path, magic=self.magic)

    def test_rename_same(self):
        self.assertTrue(self.mhdl.rename(self.mhdl.path))
