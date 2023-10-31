# coding:utf-8

import unittest

from mock import PropertyMock
from mock import patch

from strie.store.dfile import dhdl
from strie.store.dfile import didx


class test_didx(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.offset = dhdl.SIZE_MAGIC

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_check_offset(self):
        mock_offset = PropertyMock(return_value=0)
        with patch.object(didx, "offset", mock_offset):
            index = didx.new(self.offset, "test".encode())
            self.assertFalse(index.check())

    def test_check_length(self):
        mock_length = PropertyMock(return_value=0)
        with patch.object(didx, "length", mock_length):
            index = didx.new(self.offset, "test".encode())
            self.assertFalse(index.check())

    def test_check_chksum(self):
        mock_chksum = PropertyMock(return_value=-1)
        with patch.object(didx, "chksum", mock_chksum):
            index = didx.new(self.offset, "test".encode())
            self.assertFalse(index.check())
