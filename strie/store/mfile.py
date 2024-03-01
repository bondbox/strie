# coding:utf-8

import hashlib
import os
import shutil
from typing import BinaryIO
from typing import Optional


def md5sum(file: str) -> str:
    assert isinstance(file, str), f"unexpected type: {type(file)}"
    with open(file, "rb") as fhdl:
        md5_hash = hashlib.md5()
        while True:
            data = fhdl.read(1024**2)
            if not data:
                break
            md5_hash.update(data)
    return md5_hash.hexdigest()


class mhdl:
    """Magic-based file handle
    """

    def __init__(self, path: str, magic: bytes, readonly: bool = True):
        assert isinstance(path, str), f"unexpected type: {type(path)}"
        assert isinstance(magic, bytes), f"unexpected type: {type(magic)}"
        assert isinstance(readonly, bool), f"unexpected type: {type(readonly)}"
        msize: int = len(magic)
        assert msize > 0, f"size {msize} error"

        def open_check(readonly: bool) -> bool:
            if not readonly:
                # Check backup before writing
                assert not os.path.exists(self.bakpath), \
                    f"Backup {self.bakpath} exists"
            return os.path.exists(self.path)

        self.__path: str = path
        self.__msize: int = msize
        self.__magic: bytes = magic
        self.__readonly: bool = readonly
        create: bool = not open_check(readonly)  # Check backup before open
        handle: BinaryIO = open(path, "rb" if self.readonly else "ab+")
        if create and not self.readonly:
            assert handle.write(self.__magic) == self.__msize
        self.__handle: Optional[BinaryIO] = handle
        self.__endpos: int = handle.seek(0, 2)
        assert self.check(), f"{self.__path} check failed"

    def __del__(self):
        assert self.close(), f"close '{self.path}' error"

    def sync(self):
        if self.__handle is not None and not self.readonly:
            os.fsync(self.__handle)

    def close(self) -> bool:
        if self.__handle is not None:
            if not self.readonly:
                os.fsync(self.__handle)
            self.__handle.close()
            self.__handle = None
            self.__endpos = -1
        return self.__handle is None

    def reopen(self, path: Optional[str] = None) -> bool:
        if path is None:
            path = self.path
        assert isinstance(path, str), f"unexpected type: {type(path)}"
        # Not create new file
        if not os.path.isfile(path):
            return False
        # Close current file before open another
        if self.path != path:
            self.close()
        if self.__handle is None:
            assert os.path.isfile(path), f"'{path}' is not a regular file"
            assert not os.path.exists(self.bakpath), \
                f"backup file '{self.bakpath}' still exists"
            handle: BinaryIO = open(path, "rb" if self.readonly else "ab+")
            if handle is None:
                return False
            self.__handle = handle
            self.__endpos = handle.seek(0, 2)
            assert self.check()
        # Success and modify path
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        self.__path = path
        return True

    def check(self) -> bool:
        if self.__handle is None:
            return False
        if self.endpos < self.msize:
            return False
        if self.__handle.seek(0, 0) != 0:
            return False
        return self.__handle.read(self.__msize) == self.__magic

    @property
    def path(self) -> str:
        return self.__path

    @property
    def bakpath(self) -> str:
        return self.get_bakpath(self.path)

    @property
    def readonly(self) -> bool:
        return self.__readonly

    @property
    def endpos(self) -> int:
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        return self.__endpos

    @property
    def msize(self) -> int:
        return self.__msize

    @property
    def magic(self) -> bytes:
        return self.__magic

    def tell(self) -> int:
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        return self.__handle.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        return self.__handle.seek(offset, whence)

    def read(self, length: int) -> bytes:
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        assert isinstance(length, int), f"unexpected type: {type(length)}"
        assert length > 0, f"read {self.path} length {length} error"
        value: bytes = self.__handle.read(length)
        assert isinstance(value, bytes), f"unexpected type: {type(value)}"
        assert len(value) == length, f"read {self.path} length {length} error"
        return value

    def write(self, value: bytes) -> int:
        assert isinstance(value, bytes), f"unexpected type: {type(value)}"
        assert self.__handle is not None, f"Invalid file {self.path} handle"
        assert self.__readonly is False, f"Write read-only file {self.path}"
        offset: int = self.endpos
        length: int = len(value)
        assert length > 0, f"write {self.path} length {length} error"
        assert self.__handle.seek(0, 2) == offset, f"{self.path} "\
            f"{offset} != {self.__handle.tell()}, length {length}"

        try:
            return self.__handle.write(value)
        finally:
            self.__endpos = self.__handle.seek(0, 2)

    def rename(self, path: str, reopen: bool = True) -> bool:
        """Rename and reopen
        """
        assert isinstance(path, str), f"unexpected type: {type(path)}"
        assert isinstance(reopen, bool), f"unexpected type: {type(reopen)}"
        if self.path == path:
            return True
        assert not os.path.exists(path), f"{path} already exists"
        assert os.path.isfile(self.path), f"Non-existent {self.path}"
        self.close()  # close before move
        assert shutil.move(src=self.path, dst=path) == path
        assert os.path.isfile(path), f"Non-existent {path}"
        assert not os.path.exists(self.path), f"{self.path} still exists"
        return True if not reopen else self.reopen(path)

    def backup(self) -> bool:
        """Close and backup
        """
        return self.rename(self.bakpath, False)

    @classmethod
    def get_bakpath(cls, path: str) -> str:
        assert isinstance(path, str), f"unexpected type: {type(path)}"
        return f"{path}.bak"
