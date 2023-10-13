# coding:utf-8

import os
from typing import Dict
from typing import Generic
from typing import Sequence
from typing import TypeVar

from cachetools import LFUCache
from cachetools import LRUCache

from ..store import dhdl
from ..store import didx
from ..store import ihdl
from ..store import nhdl
from ..utils import testckey
from .rtree import radix
from .rtree import testskey

KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


class store(Dict[str, bytes]):
    """
    Store radix trees
    """

    def __init__(self,
                 name: str,
                 ipath: str,
                 dpath: str,
                 test: testckey,
                 readonly: bool = True):
        assert isinstance(ipath, str)
        assert isinstance(dpath, str)
        assert isinstance(readonly, bool)
        self.__readonly: bool = readonly
        self.__root: radix[didx] = radix(prefix=name, test=test)
        self.__index: ihdl = ihdl(path=ipath, readonly=readonly)
        self.__datas: dhdl = dhdl(path=dpath, readonly=readonly)
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
            assert isinstance(v, didx)
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

    def put(self, key: str, value: bytes) -> bool:
        assert not self.readonly
        assert isinstance(key, str)
        assert isinstance(value, bytes)
        info: didx = didx.new(offset=self.__datas.dump(value), value=value)
        assert isinstance(info, didx)
        self.__root[key] = info
        return self.__dump_index(key)

    def get(self, key: str) -> bytes:
        assert isinstance(key, str)
        info: didx = self.__root[key]
        assert isinstance(info, didx)
        data = self.__datas.load(offset=info.offset, length=info.length)
        assert info.check(data)
        return data

    def pop(self, key: str) -> bool:
        assert not self.readonly
        del self.__root[key]
        return self.__dump_index(key, True)


class cache(Generic[KT, VT]):

    MINIMUM = 100

    def __init__(self, cachemax: int):
        assert isinstance(cachemax, int)
        assert cachemax >= self.MINIMUM
        nlru: int = int(cachemax * 40 / 100)
        self.__clru: LRUCache[KT, VT] = LRUCache(maxsize=nlru)
        self.__clfu: LFUCache[KT, VT] = LFUCache(maxsize=cachemax - nlru)

    def __contains__(self, key: KT) -> bool:
        return key in self.__clru or key in self.__clfu

    def __getitem__(self, key: KT) -> VT:
        if key in self.__clru:
            value = self.__clru[key]
            if key not in self.__clfu:
                self.__clfu[key] = value
            assert self.__clfu[key] is value
        elif key in self.__clfu:
            value = self.__clfu[key]
            self.__clru[key] = value
        return self.__clfu[key]

    def __setitem__(self, key: KT, value: VT):
        if key in self.__clfu:
            self.__clfu[key] = value
        self.__clru[key] = value

    def __delitem__(self, key: KT):
        if key in self.__clfu:
            del self.__clfu[key]
        if key in self.__clru:
            del self.__clru[key]
        assert key not in self.__clfu
        assert key not in self.__clru


class ctrie:
    """
    Caching and persisting radix trees
    """

    MAX_NODES = 10**3  # TODO: OSError: [Errno 24] Too many open files
    MIN_NODES = 10**2

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
        self.__names: nhdl = nhdl(path=self.__path,
                                  word=word,
                                  test=test,
                                  readonly=readonly)
        cacheobj: int = min(max(int(self.__names.nodes / 2), self.MIN_NODES),
                            self.MAX_NODES)
        self.__scache: cache[str, store] = cache(max(cacheobj, cache.MINIMUM))
        self.__dcache: cache[str, bytes] = cache(max(cachemax, cache.MINIMUM))
        self.__readonly: bool = readonly

    def __contains__(self, key: str) -> bool:
        assert isinstance(key, str)
        return key in self.__route(key)

    def __setitem__(self, key: str, value: bytes):
        assert isinstance(key, str)
        assert isinstance(value, bytes)

        if key in self.__dcache:
            cache: bytes = self.__dcache[key]
            assert isinstance(cache, bytes)
            if cache == value:
                return

        try:
            assert self.__route(key).put(key=key, value=value)
            self.__dcache[key] = value  # cache value
        except Exception as e:
            if key in self.__dcache:
                del self.__dcache[key]
            raise e

    def __getitem__(self, key: str) -> bytes:
        assert isinstance(key, str)
        if key not in self.__dcache:
            self.__dcache[key] = self.__route(key).get(key=key)
        value: bytes = self.__dcache[key]
        assert isinstance(value, bytes)
        return value

    def __delitem__(self, key: str):
        assert isinstance(key, str)
        if key in self.__dcache:
            del self.__dcache[key]
        assert self.__route(key).pop(key=key)

    def __get_store(self, name: str) -> store:
        path: str = self.__names[name]
        ipath: str = f"{path}.idx"
        dpath: str = f"{path}.dat"
        return store(name=name,
                     ipath=ipath,
                     dpath=dpath,
                     test=self.__names.test,
                     readonly=self.__readonly)

    def __route(self, key: str) -> store:
        name: str = self.__names.get_name(key)
        stor: store = self.__scache[
            name] if name in self.__scache else self.__get_store(name)
        assert isinstance(stor, store)
        if name not in self.__scache:
            self.__scache[name] = stor
        return stor
