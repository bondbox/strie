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
from typing import List
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
    SIZE_SUPER = 4096
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
        assert self.__check(key), f"'{key}' illegal"
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

    @classmethod
    def file(cls, path: str) -> str:
        assert isinstance(path, str)
        if not os.path.exists(path):
            os.makedirs(path)
        assert os.path.isdir(path)
        return os.path.join(path, __prog__)

    @classmethod
    def init(cls, path: str, word: Sequence[int], test: testakey) -> bool:
        assert isinstance(path, str)
        assert isinstance(word, Sequence)
        assert isinstance(test, testakey)

        file: str = cls.file(path)
        if os.path.exists(file):
            return False

        chrs: List[int] = [ord(i) for i in test.characters]
        numc: int = len(chrs)
        numw: int = len(word)

        assert numw < 256
        for i in word:
            assert isinstance(i, int)
            assert i > 0 and i < 256

        class superblock(Structure):

            _fields_ = [
                ("magic", uint8_t * cls.SIZE_MAGIC),
                ("charn", uint8_t),
                ("wordn", uint8_t),
                ("chars", uint8_t * numc),
                ("words", uint8_t * numw),
                ("length", uint16_t),
            ]

        dat: superblock = superblock()
        siz: int = sizeof(superblock)
        assert siz <= cls.SIZE_SUPER

        dat.magic = (uint8_t * cls.SIZE_MAGIC)(*cls.MAGIC)
        dat.charn = numc
        dat.wordn = numw
        for i in range(numc):
            dat.chars[i] = chrs[i]
        for i in range(numw):
            dat.words[i] = word[i]
        dat.length = sum(word)

        ctx = bytes(dat) + bytes(cls.SIZE_SUPER - siz)
        assert len(ctx) == cls.SIZE_SUPER
        assert os.path.isdir(path)
        assert not os.path.exists(file)
        with open(file, "wb") as hdl:
            if hdl.write(ctx) != cls.SIZE_SUPER:
                return False
        return True

    @classmethod
    def load(cls, path: str, readonly: bool = True) -> "nhdl":

        file: str = cls.file(path)
        assert os.path.isfile(file)

        def read_head():

            class head(Structure):

                _fields_ = [
                    ("magic", uint8_t * cls.SIZE_MAGIC),
                    ("charn", uint8_t),
                    ("wordn", uint8_t),
                ]

            dat: head = head()
            siz: int = sizeof(head)

            with open(file, "rb") as hdl:
                ctx = hdl.read(siz)
                ptr = (c_char * siz).from_buffer(bytearray(ctx))
                memmove(addressof(dat), ptr, siz)
                assert bytes(dat.magic) == cls.MAGIC
                return dat

        def read_superblock(numc: int, numw: int):

            class superblock(Structure):

                _fields_ = [
                    ("magic", uint8_t * cls.SIZE_MAGIC),
                    ("charn", uint8_t),
                    ("wordn", uint8_t),
                    ("chars", uint8_t * numc),
                    ("words", uint8_t * numw),
                    ("length", uint16_t),
                ]

            dat: superblock = superblock()
            siz: int = sizeof(superblock)

            with open(file, "rb") as hdl:
                ctx = hdl.read(siz)
                ptr = (c_char * siz).from_buffer(bytearray(ctx))
                memmove(addressof(dat), ptr, siz)
                assert bytes(dat.magic) == cls.MAGIC
                assert dat.length == sum(dat.words)
                assert dat.charn == numc
                assert dat.wordn == numw
                return dat

        head = read_head()
        sb = read_superblock(numc=head.charn, numw=head.wordn)
        test: testakey = testakey(allowed_char={chr(c) for c in sb.chars})
        word: Sequence[int] = tuple(w for w in sb.words)
        return nhdl(path=path, word=word, test=test, readonly=readonly)

    def __load(self) -> bool:
        if self.endpos > self.SIZE_MAGIC:
            assert self.endpos >= self.SIZE_SUPER
            assert self.seek(self.SIZE_SUPER) == self.SIZE_SUPER
            # read all names
            while self.tell() < self.endpos:
                name: str = self.read(self.length).decode()
                assert self.read(self.SIZE_MAGIC) == self.MAGIC
                self.__names[name] = self.get_path(name)
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
