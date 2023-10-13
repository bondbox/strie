# coding:utf-8

from ctypes import c_uint8
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import c_uint64
import os
from typing import BinaryIO
from typing import Optional

uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
uint64_t = c_uint64


class mhdl:
    '''
    Magic-based file handle
    '''

    def __init__(self, path: str, magic: bytes, readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(magic, bytes)
        assert isinstance(readonly, bool)
        create: bool = not os.path.exists(path)
        handle: BinaryIO = open(path, "rb" if readonly else "ab+")
        self.__path: str = path
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
    def path(self) -> str:
        return self.__path

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

    @property
    def magic(self) -> bytes:
        return self.__magic

    @property
    def msize(self) -> int:
        return self.__msize
