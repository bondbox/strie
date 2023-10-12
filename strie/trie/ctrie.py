# coding:utf-8

import os
from typing import Optional
from typing import Sequence

from cachetools import LFUCache
from cachetools import LRUCache

from ..utils import testckey
from .radix import radix
from .radix import testskey
from .store import dfile
from .store import ifile
from .store import index
from .store import nfile


class store:

    def __init__(self,
                 name: str,
                 index: str,
                 datas: str,
                 test: testckey,
                 cachelru: int = 200,
                 cachelfu: int = 800,
                 readonly: bool = True):
        assert isinstance(index, str)
        assert isinstance(datas, str)
        assert isinstance(cachelru, int)
        assert isinstance(cachelfu, int)
        assert isinstance(readonly, bool)
        assert cachelfu >= cachelru
        self.__readonly: bool = readonly
        self.__root: radix = radix(prefix=name, test=test)
        self.__clru: Optional[LRUCache[str, bytes]] = LRUCache(
            maxsize=cachelru) if cachelru > 1 else None
        self.__clfu: Optional[LFUCache[str, bytes]] = LFUCache(
            maxsize=cachelfu) if cachelfu > 1 else None
        self.__index: ifile = ifile(path=index, readonly=readonly)
        self.__datas: dfile = dfile(path=datas, readonly=readonly)
        assert self.__load_index()

    def __del__(self):
        # TODO: GC
        pass

    @property
    def readonly(self) -> bool:
        return self.__readonly

    def __len__(self) -> int:
        return len(self.__root)

    def __iter__(self):
        iter(self.__root)
        return self.__root

    def __contains__(self, key: str) -> bool:
        return key in self.__root

    def __setitem__(self, key: str, value: bytes):
        assert self.put(key=key, value=value)

    def __getitem__(self, key: str) -> bytes:
        return self.get(key=key)

    def __delitem__(self, key: str):
        assert self.pop(key=key)

    def __load_index(self) -> bool:
        prefix: str = self.__root.prefix
        for k, v in self.__index:
            key = prefix + k
            assert isinstance(key, str)
            if v is None:
                assert key in self.__root
                del self.__root[key]
                continue
            assert isinstance(v, index)
            self.__root[key] = v
        return True

    def __dump_index(self, key: str, delete: bool = False) -> bool:
        assert not self.readonly
        assert isinstance(key, str)
        assert isinstance(delete, bool)
        if delete is True:
            # delete key
            assert self.__index.dump(self.__root.nick(key), None)
        else:
            # create or update key
            assert self.__index.dump(self.__root.nick(key), self.__root[key])
        return True

    def put(self, key: str, value: bytes, cache: bool = True) -> bool:
        assert not self.readonly
        assert isinstance(key, str)
        assert isinstance(value, bytes)
        assert isinstance(cache, bool)
        if key in self.__root and self.get(key=key, cache=True) == value:
            # No need to update the same value
            return True
        info: index = index.new(offset=self.__datas.dump(value), value=value)
        assert isinstance(info, index)
        self.__root[key] = info
        if self.__clru is not None:
            assert self.__clfu is not None
            if key in self.__clfu:
                if cache is True:
                    self.__clfu[key] = value
                else:
                    del self.__clfu[key]
            elif key in self.__clru:
                if cache is True:
                    self.__clru[key] = value
                else:
                    del self.__clfu[key]
            elif cache is True:
                self.__clru[key] = value
        return self.__dump_index(key)

    def get(self, key: str, cache: bool = True) -> bytes:
        assert isinstance(key, str)
        assert isinstance(cache, bool)
        if self.__clfu is not None and key in self.__clfu:
            return self.__clfu[key]
        if self.__clru is not None and key in self.__clru:
            assert self.__clfu is not None
            data: bytes = self.__clru[key]
            assert isinstance(data, bytes)
            self.__clfu[key] = data
            del self.__clru[key]
            return self.__clfu[key]
        info: index = self.__root[key]
        assert isinstance(info, index)
        data = self.__datas.load(offset=info.offset, length=info.length)
        assert info.check(data)
        if cache is True and self.__clru is not None:
            self.__clru[key] = data
        return data

    def pop(self, key: str) -> bool:
        assert not self.readonly
        if self.__clru is not None and key in self.__clru:
            del self.__clru[key]
        if self.__clfu is not None and key in self.__clfu:
            del self.__clfu[key]
        del self.__root[key]
        return self.__dump_index(key, True)


class ctrie:
    """
    Caching and persisting radix trees
    """

    MAX_NODES = 10**3  # TODO: OSError: [Errno 24] Too many open files
    MIN_NODES = 10**1
    MIN_CACHE = 10**2

    def __init__(self,
                 path: str = ".",
                 word: Sequence[int] = (2, ),
                 test: testckey = testskey,
                 cachemax: int = 10**6,
                 readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(cachemax, int)
        assert isinstance(readonly, bool)
        if not os.path.exists(path):
            os.makedirs(path)
        assert os.path.isdir(path)
        self.__path: str = path
        self.__names: nfile = nfile(path=self.__path,
                                    word=word,
                                    test=test,
                                    readonly=readonly)
        cacheobj: int = min(int(self.__names.nodes / 2), self.MAX_NODES)
        cachekey: int = max(int(cachemax / cacheobj / 5), self.MIN_CACHE)
        self.__clru: LRUCache[str, store] = LRUCache(
            maxsize=cacheobj if cacheobj > self.MIN_NODES else self.MIN_NODES)
        self.__clfu: LFUCache[str, store] = LFUCache(
            maxsize=cacheobj if cacheobj > self.MIN_NODES else self.MIN_NODES)
        self.__cachelfu: int = cachekey * 4
        self.__cachelru: int = cachekey
        self.__readonly: bool = readonly

    def __contains__(self, key: str) -> bool:
        return key in self.__route(key)

    def __setitem__(self, key: str, value: bytes):
        assert self.__route(key).put(key=key, value=value)

    def __getitem__(self, key: str) -> bytes:
        return self.__route(key).get(key=key)

    def __delitem__(self, key: str):
        assert self.__route(key).pop(key=key)

    def __get_store(self, name: str) -> store:
        path: str = self.__names[name]
        index: str = f"{path}.idx"
        datas: str = f"{path}.dat"
        return store(name=name,
                     index=index,
                     datas=datas,
                     test=self.__names.test,
                     cachelru=self.__cachelru,
                     cachelfu=self.__cachelfu,
                     readonly=self.__readonly)

    def __route(self, key: str) -> store:
        name: str = self.__names.get_name(key)
        if name in self.__clfu:
            return self.__clfu[name]
        if name in self.__clru:
            assert name not in self.__clfu
            stor: store = self.__clru[name]
            assert isinstance(stor, store)
            self.__clfu[name] = stor
            del self.__clru[name]
            return self.__clfu[name]
        stor: store = self.__get_store(name)
        assert isinstance(stor, store)
        self.__clru[name] = stor
        return stor
