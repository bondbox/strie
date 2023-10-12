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
import os
from typing import BinaryIO
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

from ..utils import __prog__
from ..utils import testckey

uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
uint64_t = c_uint64


class index:

    class data(Structure):

        _fields_ = [
            ('offset', uint64_t),
            ('length', uint32_t),
            ('chksum', uint32_t),
        ]

    SIZE_DATA = sizeof(data)

    def __init__(self, offset: int, length: int, chksum: int = 0):
        assert isinstance(offset, int) and offset >= ifile.SIZE_MAGIC
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

    @chksum.setter
    def chksum(self, value: bytes):
        assert isinstance(value, bytes)
        self.__data.chksum = binascii.crc32(value)

    def check(self, value: bytes) -> bool:
        assert isinstance(value, bytes)
        return binascii.crc32(value) == self.__data.chksum

    def dump(self) -> bytes:
        return bytes(self.__data)

    @classmethod
    def load(cls, value: bytes) -> "index":
        assert len(value) == cls.SIZE_DATA
        dat = cls.data()
        ptr = (c_char * cls.SIZE_DATA).from_buffer(bytearray(value))
        memmove(addressof(dat), ptr, cls.SIZE_DATA)
        return index(offset=dat.offset, length=dat.length, chksum=dat.chksum)

    @classmethod
    def new(cls, offset: int, value: bytes) -> "index":
        return index(offset=offset,
                     length=len(value),
                     chksum=binascii.crc32(value))


class mfile:
    '''
    Magic-based file
    '''

    def __init__(self, path: str, magic: bytes, readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(magic, bytes)
        assert isinstance(readonly, bool)
        create: bool = not os.path.exists(path)
        handle: BinaryIO = open(path, "rb" if readonly else "ab+")
        self.__magic: bytes = magic
        self.__msize: int = len(magic)
        if create:
            assert handle.write(self.__magic) == self.__msize
        self.__endpos: int = handle.tell()
        assert self.__endpos >= self.__msize
        self.__handle: Optional[BinaryIO] = handle
        assert self.check()

    def __del__(self):
        self.sync()
        self.close()

    def sync(self):
        if self.handle is not None:
            os.fsync(self.handle)

    def close(self):
        if self.handle is not None:
            self.handle.close()
            self.handle = None
            self.endpos = -1

    def check(self) -> bool:
        if self.handle is None:
            return False
        if self.handle.seek(0, 0) != 0:
            return False
        return self.handle.read(self.__msize) == self.__magic

    @property
    def handle(self) -> Optional[BinaryIO]:
        return self.__handle

    @handle.setter
    def handle(self, v: Optional[BinaryIO]):
        if v is not None:
            assert isinstance(v, BinaryIO)
            assert v.seek(0, 0) == 0
            assert v.read(self.__msize) == self.__magic
        self.__handle = v

    @property
    def endpos(self) -> int:
        assert self.__handle is not None
        return self.__endpos

    @endpos.setter
    def endpos(self, v: int):
        if v > 0:
            assert self.__handle is not None
        else:
            assert self.__handle is None
        self.__endpos = v


class ifile(mfile):
    '''
    Index file
    '''

    class head(Structure):
        _fields_ = [
            ('keylen', uint32_t, 16),
            ('delkey', uint32_t, 1),
        ]

    SIZE_HEAD = sizeof(head)

    MAGIC = b"\x3a\x37\xc5\xb2\x9e\x5c\x2a\xa3"
    SIZE_MAGIC = len(MAGIC)

    def __init__(self, path: str, readonly: bool = True):
        super().__init__(path=path, magic=self.MAGIC, readonly=readonly)

    def __iter__(self):
        assert self.check()
        return self

    def __next__(self) -> Tuple[str, Optional[index]]:
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        if hdl.tell() < self.endpos:
            return self.__load()
        raise StopIteration

    def __load(self) -> Tuple[str, Optional[index]]:
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
        idx = index.load(hdl.read(index.SIZE_DATA))
        return key, idx

    def dump(self, key: str, value: Optional[index]) -> bool:
        assert isinstance(key, str)
        assert isinstance(value, index) or value is None
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
            assert isinstance(value, index)
            assert hdl.write(value.dump()) == index.SIZE_DATA
            self.endpos += index.SIZE_DATA
        return True


class dfile(mfile):
    '''
    Datas file
    '''

    MAGIC = b"\x3a\x2c\xc5\xe2\x68\x5c\x12\xa3"
    SIZE_MAGIC = len(MAGIC)

    def __init__(self, path: str, readonly: bool = True):
        super().__init__(path=path, magic=self.MAGIC, readonly=readonly)

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


class nfile(mfile):
    '''
    Names file
    '''

    MAGIC = b"\x3a\x33\xc5\xf9\x8b\x5c\x73\xa3"
    SIZE_MAGIC = len(MAGIC)
    MAX_FILES = 10**6

    def __init__(self,
                 path: str,
                 word: Sequence[int],
                 test: testckey,
                 readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(word, Sequence)
        assert isinstance(test, testckey)
        assert os.path.isdir(path)
        self.__path: str = path
        self.__test: testckey = test
        self.__word: Sequence[int] = tuple(int(i) for i in word)
        for i in self.__word:
            assert i > 0 and i < 256  # 1-255: 1 byte
        self.__length: int = sum(self.__word)
        self.__names: Dict[str, str] = {}
        self.__nodes: int = len(self.__test.characters)**self.length
        assert self.__nodes <= self.MAX_FILES
        super().__init__(path=os.path.join(self.__path, __prog__),
                         magic=self.MAGIC,
                         readonly=readonly)
        assert self.__load(True if self.endpos > self.SIZE_MAGIC else False)

    @property
    def test(self) -> testckey:
        return self.__test

    @property
    def nodes(self) -> int:
        return self.__nodes

    @property
    def length(self) -> int:
        return self.__length

    def __iter__(self):
        return iter(self.__names)

    def __contains__(self, name: str) -> bool:
        return name in self.__names

    def __getitem__(self, name: str) -> str:
        if name not in self.__names:
            self.__dump(name)
        return self.__names[name]

    def __check(self, key: str) -> bool:
        if not isinstance(key, str):
            return False
        if len(key) < self.length:
            return False
        return self.test.check(key)

    def get_name(self, key: str) -> str:
        assert self.__check(key)
        return key[:self.length]

    def get_path(self, name: str) -> str:
        assert isinstance(name, str)
        assert len(name) == self.length
        path: str = self.__path
        for i in self.__word:
            if not os.path.exists(path):
                os.mkdir(path)
            assert os.path.isdir(path)
            path = os.path.join(path, name[:i])
            name = name[i:]
        return path

    def __load(self, read: bool = True) -> bool:

        num: int = len(self.__word)

        class head(Structure):

            _fields_ = [
                ('word', uint8_t * num),
                ('magic', uint8_t * self.SIZE_MAGIC),
            ]

        dat: head = head()
        siz: int = sizeof(head)
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.tell() == self.SIZE_MAGIC

        if read is True:
            # read head data
            assert self.endpos >= self.SIZE_MAGIC + siz
            ctx = hdl.read(siz)
            ptr = (c_char * siz).from_buffer(bytearray(ctx))
            memmove(addressof(dat), ptr, siz)
            if bytes(dat.magic) != self.MAGIC:
                return False
            for i in range(num):
                if dat.word[i] != self.__word[i]:
                    return False
            # read all names
            while hdl.tell() < self.endpos:
                name: str = hdl.read(self.length).decode()
                assert hdl.read(self.SIZE_MAGIC) == self.MAGIC
                self.__names[name] = self.get_path(name)
        else:
            # write head data
            assert self.endpos == self.SIZE_MAGIC
            for i in range(num):
                dat.word[i] = self.__word[i]
            dat.magic = (uint8_t * self.SIZE_MAGIC)(*self.MAGIC)
            ctx = bytes(dat)
            assert len(ctx) == siz
            assert hdl.write(ctx) == siz
            self.endpos += siz

        return True

    def __dump(self, name: str) -> int:
        assert isinstance(name, str)
        assert name not in self.__names
        data: bytes = name.encode()
        offset: int = self.endpos
        length: int = len(data)
        assert length > 1
        hdl: Optional[BinaryIO] = self.handle
        assert hdl is not None
        assert hdl.seek(0, 2) == offset
        assert hdl.write(data) == length
        assert hdl.write(self.MAGIC) == self.SIZE_MAGIC
        self.__names[name] = self.get_path(name)
        self.endpos += (length + self.SIZE_MAGIC)
        return self.endpos
