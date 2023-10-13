# coding:utf-8

import binascii
from ctypes import Structure
from ctypes import addressof
from ctypes import c_char
from ctypes import c_uint8
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import c_uint64
from ctypes import memmove
from ctypes import sizeof
from typing import BinaryIO
from typing import Optional
from typing import Tuple

from .mfile import mhdl

uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
uint64_t = c_uint64


class dhdl(mhdl):
    '''
    Datas file handle
    '''

    MAGIC = b"\x3a\x2c\xc5\xe2\x68\x5c\x12\xa3"
    SIZE_MAGIC = len(MAGIC)

    def __init__(self, path: str, readonly: bool = True):
        super().__init__(path=path, magic=self.MAGIC, readonly=readonly)

    @property
    def dsize(self) -> int:
        dsize: int = self.endpos - self.msize
        assert dsize >= 0
        return dsize

    def load(self, offset: int, length: int) -> bytes:
        assert isinstance(offset, int)
        assert isinstance(length, int)
        assert offset >= self.SIZE_MAGIC
        assert length > 0
        assert offset + length <= self.endpos
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.seek(offset) == offset
        assert hdl.tell() == offset
        return hdl.read(length)

    def dump(self, value: bytes) -> int:
        assert isinstance(value, bytes)
        offset: int = self.endpos
        length: int = len(value)
        assert length > 0
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.seek(0, 2) == offset
        assert hdl.write(value) == length
        self.endpos += length
        return offset


class didx:
    '''
    Datas index
    '''

    class data(Structure):

        _fields_ = [
            ("offset", uint64_t),
            ("length", uint32_t),
            ("chksum", uint32_t),
        ]

    SIZE_DATA = sizeof(data)

    def __init__(self, offset: int, length: int, chksum: int = 0):
        assert isinstance(offset, int) and offset >= ihdl.SIZE_MAGIC
        assert isinstance(length, int) and length > 0
        assert isinstance(chksum, int)
        self.__data = self.data()
        self.__data.offset = offset
        self.__data.length = length
        self.__data.chksum = chksum

    @property
    def offset(self) -> int:
        return self.__data.offset

    @property
    def length(self) -> int:
        return self.__data.length

    @property
    def chksum(self) -> int:
        return self.__data.chksum

    def check(self, value: bytes) -> bool:
        assert isinstance(value, bytes)
        return binascii.crc32(value) == self.__data.chksum

    def dump(self) -> bytes:
        return bytes(self.__data)

    @classmethod
    def load(cls, value: bytes) -> "didx":
        assert len(value) == cls.SIZE_DATA
        dat = cls.data()
        ptr = (c_char * cls.SIZE_DATA).from_buffer(bytearray(value))
        memmove(addressof(dat), ptr, cls.SIZE_DATA)
        return didx(offset=dat.offset, length=dat.length, chksum=dat.chksum)

    @classmethod
    def new(cls, offset: int, value: bytes) -> "didx":
        return didx(offset=offset,
                    length=len(value),
                    chksum=binascii.crc32(value))


class ihdl(mhdl):
    '''
    Datas index file handle
    '''

    class head(Structure):
        _fields_ = [
            ("keylen", uint32_t, 16),
            ("delkey", uint32_t, 1),
        ]

    SIZE_HEAD = sizeof(head)

    MAGIC = b"\x3a\x37\xc5\xb2\x9e\x5c\x2a\xa3"
    SIZE_MAGIC = len(MAGIC)

    def __init__(self, path: str, readonly: bool = True):
        super().__init__(path=path, magic=self.MAGIC, readonly=readonly)

    def __iter__(self):
        assert self.check()
        return self

    def __next__(self) -> Tuple[str, Optional[didx]]:
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        if hdl.tell() < self.endpos:
            return self.__load()
        raise StopIteration

    def __load(self) -> Tuple[str, Optional[didx]]:
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.tell() < self.endpos
        res = self.head()
        ctx = hdl.read(self.SIZE_HEAD)
        ptr = (c_char * self.SIZE_HEAD).from_buffer(bytearray(ctx))
        memmove(addressof(res), ptr, self.SIZE_HEAD)
        length: int = res.keylen
        key: str = hdl.read(length).decode() if length >= 0 else ""
        if res.delkey:
            return key, None
        idx = didx.load(hdl.read(didx.SIZE_DATA))
        return key, idx

    def dump(self, key: str, value: Optional[didx]) -> bool:
        assert isinstance(key, str)
        assert isinstance(value, didx) or value is None
        delete: bool = True if value is None else False
        res = self.head()
        res.keylen = len(key)
        res.delkey = delete
        ctx = bytes(res)
        assert len(ctx) == self.SIZE_HEAD
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.seek(0, 2) == self.endpos
        assert hdl.write(ctx) == self.SIZE_HEAD
        self.endpos += self.SIZE_HEAD
        dat = key.encode()
        assert hdl.write(dat) == len(dat)
        self.endpos += len(dat)
        if not delete:
            assert isinstance(value, didx)
            assert hdl.write(value.dump()) == didx.SIZE_DATA
            self.endpos += didx.SIZE_DATA
        return True
