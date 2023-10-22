# coding:utf-8

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
from typing import Dict
from typing import Sequence

from ..utils import __prog__
from ..utils import testakey
from .mfile import mhdl

uint8_t = c_uint8
uint16_t = c_uint16
uint32_t = c_uint32
uint64_t = c_uint64


class nhdl(mhdl):
    '''
    Names file handle
    '''

    MAGIC = b"\x3a\x33\xc5\xf9\x8b\x5c\x73\xa3"
    SIZE_MAGIC = len(MAGIC)
    MAX_FILES = 10**6

    def __init__(self,
                 path: str,
                 word: Sequence[int],
                 test: testakey,
                 readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(word, Sequence)
        assert isinstance(test, testakey)
        assert os.path.isdir(path)
        self.__path: str = path
        self.__test: testakey = test
        self.__word: Sequence[int] = tuple(int(i) for i in word)
        for i in self.__word:
            assert i > 0 and i < 256  # 1-255: 1 byte
        self.__length: int = sum(self.__word)
        self.__names: Dict[str, str] = {}
        self.__nodes: int = len(self.__test.characters)**self.length
        assert self.__nodes <= self.MAX_FILES, \
            f"{self.__nodes} more than {self.MAX_FILES}, please reduce word!"
        super().__init__(path=os.path.join(self.__path, __prog__),
                         magic=self.MAGIC,
                         readonly=readonly)
        assert self.__load()

    @property
    def test(self) -> testakey:
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

    def __load(self) -> bool:
        num: int = len(self.__word)

        class head(Structure):

            _fields_ = [
                ('word', uint8_t * num),
                ('magic', uint8_t * self.SIZE_MAGIC),
            ]

        dat: head = head()
        siz: int = sizeof(head)

        if self.endpos > self.SIZE_MAGIC:
            # read head data
            assert self.tell() == self.SIZE_MAGIC
            assert self.endpos >= self.SIZE_MAGIC + siz
            ctx = self.read(siz)
            ptr = (c_char * siz).from_buffer(bytearray(ctx))
            memmove(addressof(dat), ptr, siz)
            if bytes(dat.magic) != self.MAGIC:
                return False
            for i in range(num):
                if dat.word[i] != self.__word[i]:
                    return False
            # read all names
            while self.tell() < self.endpos:
                name: str = self.read(self.length).decode()
                assert self.read(self.SIZE_MAGIC) == self.MAGIC
                self.__names[name] = self.get_path(name)
        else:
            # write head data
            assert self.endpos == self.SIZE_MAGIC
            for i in range(num):
                dat.word[i] = self.__word[i]
            dat.magic = (uint8_t * self.SIZE_MAGIC)(*self.MAGIC)
            ctx = bytes(dat)
            assert len(ctx) == siz
            assert self.write(ctx) == siz

        return True

    def __dump(self, name: str) -> int:
        assert isinstance(name, str)
        assert name not in self.__names
        data: bytes = name.encode() + self.MAGIC
        length: int = len(data)
        assert length > self.SIZE_MAGIC
        assert self.write(data) == length
        self.__names[name] = self.get_path(name)
        return self.endpos
