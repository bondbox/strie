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
        assert self.seek(offset) == offset
        assert self.tell() == offset
        return self.read(length)

    def dump(self, value: bytes) -> int:
        length: int = len(value)
        assert self.write(value) == length
        return self.endpos - length


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

    def __init__(self, offset: int, length: int, chksum: int = -1):
        assert isinstance(offset, int), f"unexpected type: {type(offset)}"
        assert isinstance(length, int), f"unexpected type: {type(offset)}"
        assert isinstance(chksum, int), f"unexpected type: {type(chksum)}"
        assert offset >= dhdl.SIZE_MAGIC, \
            f"offset {offset} < {dhdl.SIZE_MAGIC}"
        assert length > 0, f"length {length} error"
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

    @classmethod
    def calc(cls, value: bytes) -> int:
        assert isinstance(value, bytes)
        return binascii.crc32(value)

    def check(self) -> bool:
        if self.offset < dhdl.SIZE_MAGIC:
            return False
        if self.length <= 0:
            return False
        if self.chksum < 0:
            return False
        return True

    def verify(self, value: bytes) -> bool:
        return self.calc(value) == self.__data.chksum

    def dump(self) -> bytes:
        assert self.check()
        return bytes(self.__data)

    @classmethod
    def load(cls, value: bytes) -> Optional["didx"]:
        assert len(value) == cls.SIZE_DATA, f"{value} != {cls.SIZE_DATA}"
        dat = cls.data()
        ptr = (c_char * cls.SIZE_DATA).from_buffer(bytearray(value))
        memmove(addressof(dat), ptr, cls.SIZE_DATA)
        return None if dat.offset == 0 and dat.length == 0 and dat.chksum == 0\
            else didx(offset=dat.offset, length=dat.length, chksum=dat.chksum)

    @classmethod
    def new(cls, offset: int, value: bytes) -> "didx":
        return didx(offset=offset, length=len(value), chksum=cls.calc(value))


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

    def __next__(self) -> Tuple[Optional[str], Optional[didx]]:
        if self.tell() < self.endpos:
            return self.__load()
        raise StopIteration

    def __load(self) -> Tuple[Optional[str], Optional[didx]]:
        assert self.tell() < self.endpos
        res = self.head()
        ctx = self.read(self.SIZE_HEAD)
        ptr = (c_char * self.SIZE_HEAD).from_buffer(bytearray(ctx))
        memmove(addressof(res), ptr, self.SIZE_HEAD)
        length: int = res.keylen
        if length <= 0:
            return None, None
        assert length > 0, f"length {length} error"
        key: str = self.read(length).decode()
        if res.delkey:
            return key, None
        idx = didx.load(self.read(didx.SIZE_DATA))
        return key, idx

    def dump(self, key: str, value: Optional[didx]) -> bool:
        assert isinstance(key, str)
        assert isinstance(value, didx) or value is None
        delete: bool = True if value is None else False
        res: ihdl.head = self.head()
        res.keylen = len(key)
        res.delkey = delete
        dat: bytes = key.encode()
        ctx: bytes = bytes(res) + dat
        num: int = self.SIZE_HEAD + len(dat)
        if not delete:
            assert isinstance(value, didx)
            ctx += value.dump()
            num += didx.SIZE_DATA
        assert len(ctx) == num
        assert self.write(ctx) == num
        return True
