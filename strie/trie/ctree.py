# coding:utf-8

import os
from tempfile import TemporaryDirectory
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import TypeVar

from cachetools import LFUCache
from cachetools import LRUCache

from ..store import dhdl
from ..store import didx
from ..store import ihdl
from ..store import mhdl
from ..store import nhdl
from ..utils import testckey
from .rtree import radix
from .rtree import testskey

KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


class cache(Generic[KT, VT]):

    MINIMUM = 100

    def __init__(self, cachemax: int):
        assert isinstance(cachemax, int)
        assert cachemax >= self.MINIMUM, f"{cachemax} less than {self.MINIMUM}"
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


class store(Dict[str, bytes]):
    """
    Store radix trees
    """

    IDX_GC_MIN_DEL = 100  # indexs
    IDX_GC_MAX_DEL = 10000  # indexs
    DAT_GC_MIN_DEL = 16 * 1024  # bytes, 16k
    DAT_GC_MAX_DEL = 64 * 1024**2  # bytes, 64m

    def __init__(self,
                 name: str,
                 ipath: str,
                 dpath: str,
                 test: testckey,
                 readonly: bool = True,
                 icache: Optional[cache[str, radix[didx]]] = None):
        assert isinstance(name, str)
        assert isinstance(icache, cache) or icache is None
        assert isinstance(readonly, bool)
        assert self.restore(ipath, dpath)
        if icache is not None and name in icache:
            index: radix[didx] = icache[name]
            reload: bool = False
        else:
            if icache is not None:
                assert name not in icache
            index: radix[didx] = radix(prefix=name, test=test)
            reload: bool = True
        assert isinstance(reload, bool)
        assert isinstance(index, radix)
        assert index.prefix == name
        assert index.test is test
        self.__name: str = name
        self.__count: int = 0
        self.__readonly: bool = readonly
        self.__index: radix[didx] = index
        self.__cache: Optional[cache[str, radix[didx]]] = icache
        self.__ihdl: ihdl = ihdl(path=ipath, readonly=readonly)
        self.__dhdl: dhdl = dhdl(path=dpath, readonly=readonly)
        if reload is True:
            assert self.__load_index()

    def __del__(self):
        if self.__cache is not None:
            self.__cache[self.__name] = self.__index

    @property
    def index(self) -> radix[didx]:
        if self.__cache is None:
            return self.__index
        if self.__name not in self.__cache:
            self.__cache[self.__name] = self.__index
        return self.__cache[self.__name]

    @property
    def readonly(self) -> bool:
        return self.__readonly

    def __len__(self) -> int:
        return len(self.index)

    def __iter__(self):
        return iter(self.index)

    def __contains__(self, key: str) -> bool:
        return key in self.index

    def __setitem__(self, key: str, value: bytes):
        assert self.put(key=key, value=value)

    def __getitem__(self, key: str) -> bytes:
        return self.get(key=key)

    def __delitem__(self, key: str):
        assert self.pop(key=key)

    def __load_index(self) -> bool:
        prefix: str = self.index.prefix
        for k, v in self.__ihdl:
            self.__count += 1
            key = prefix + k
            assert isinstance(key, str)
            if v is None:
                assert key in self.index
                del self.index[key]
                continue
            assert isinstance(v, didx)
            self.index[key] = v
        if not self.readonly:
            # gc after load index
            assert self.__gc(force=False)
        return True

    def __dump_index(self, key: str, delete: bool = False) -> bool:
        assert not self.readonly
        assert isinstance(key, str)
        assert isinstance(delete, bool)
        self.__count += 1
        if delete is True:
            # delete key
            assert self.__ihdl.dump(self.index.nick(key), None)
        else:
            # create or update key
            assert self.__ihdl.dump(self.index.nick(key), self.index[key])
        return True

    def __gc(self, force: bool = False) -> bool:
        if self.readonly is not False:
            return False

        def test_gc_datas(force: bool = False) -> bool:
            if not force:
                realsize: int = 0
                datasize: int = self.__dhdl.dsize
                for key in self.index:
                    idx: didx = self.index[key]
                    realsize += idx.length
                assert datasize >= realsize
                if datasize - realsize < self.DAT_GC_MIN_DEL:
                    return False
                elif datasize - realsize < self.DAT_GC_MAX_DEL:
                    if realsize / datasize > 0.8:
                        return False
            return True

        def test_gc_index(force: bool = False) -> bool:
            idxnum: int = len(self.index)
            assert self.__count >= idxnum, f"{self.__count} less than {idxnum}"
            if idxnum == self.__count:
                return False
            if not force:
                if self.__count - idxnum < self.IDX_GC_MIN_DEL:
                    return False
                elif self.__count - idxnum < self.IDX_GC_MAX_DEL:
                    if idxnum / self.__count > 0.8:
                        return False
            return True

        if test_gc_index(force=force):
            with TemporaryDirectory(dir=None) as tempdir:
                assert not os.path.exists(self.__ihdl.bakpath), \
                    f"Index backup {self.__ihdl.bakpath} already exists"
                assert not os.path.exists(self.__dhdl.bakpath), \
                    f"Datas backup {self.__dhdl.bakpath} already exists"
                if test_gc_datas(force=force):
                    # gc index and data
                    stor: store = store(name=self.index.prefix,
                                        ipath=os.path.join(tempdir, "idx.gc"),
                                        dpath=os.path.join(tempdir, "dat.gc"),
                                        test=self.index.test,
                                        readonly=False,
                                        icache=None)
                    for key in self:
                        datas: bytes = self.get(key)
                        assert isinstance(datas, bytes)
                        assert stor.put(key, datas)
                    # backup and update
                    assert self.__ihdl.backup(), \
                        f"Create index bcakup {self.__ihdl.bakpath} failed"
                    assert self.__dhdl.backup(), \
                        f"Create datas bcakup {self.__dhdl.bakpath} failed"
                    assert stor.__ihdl.rename(self.__ihdl.path), \
                        f"Rename to index {self.__ihdl.path} failed"
                    assert stor.__dhdl.rename(self.__dhdl.path), \
                        f"Rename to datas {self.__dhdl.path} failed"
                    # data overwritten, update index
                    self.__ihdl = stor.__ihdl
                    self.__dhdl = stor.__dhdl
                    self.__index = stor.index
                    if self.__cache is not None:
                        if self.__name in self.__cache:
                            del self.__cache[self.__name]
                        assert self.__name not in self.__cache
                        self.__cache[self.__name] = stor.index
                    os.remove(self.__ihdl.bakpath)
                    os.remove(self.__dhdl.bakpath)
                else:
                    # only gc index
                    hidx: ihdl = ihdl(path=os.path.join(tempdir, "idx.gc"),
                                      readonly=False)
                    for key in self.index:
                        index: didx = self.index[key]
                        assert isinstance(index, didx)
                        assert hidx.dump(self.index.nick(key), index)
                    # backup and update
                    assert self.__ihdl.backup(), \
                        f"Create index bcakup {self.__ihdl.bakpath} failed"
                    assert hidx.rename(self.__ihdl.path), \
                        f"Rename to index {self.__ihdl.path} failed"
                    self.__ihdl = hidx
                    os.remove(self.__ihdl.bakpath)
                assert not os.path.exists(self.__ihdl.bakpath), \
                    f"Index backup {self.__ihdl.bakpath} still exists"
                assert not os.path.exists(self.__dhdl.bakpath), \
                    f"Datas backup {self.__dhdl.bakpath} still exists"

        return True

    def force_gc(self) -> bool:
        return self.__gc(force=True)

    @classmethod
    def restore(cls, ipath: str, dpath: str) -> bool:
        ibak: str = mhdl.get_bakpath(ipath)
        dbak: str = mhdl.get_bakpath(dpath)

        def safe_remove_file(path: str) -> bool:
            assert isinstance(path, str)
            if os.path.isfile(path):
                os.remove(path)
            return not os.path.exists(path)

        def safe_rename_file(src: str, dst: str) -> bool:
            assert isinstance(src, str)
            assert isinstance(dst, str)
            assert src != dst
            assert os.path.isfile(src), f"{src}"
            assert not os.path.exists(dst), f"{dst}"
            os.rename(src=src, dst=dst)
            assert not os.path.exists(src), f"{src}"
            assert os.path.isfile(dst), f"{dst}"
            return True

        # No backup available
        if not os.path.exists(ibak) and not os.path.exists(dbak):
            return True
        # Restore backup and check
        if not os.path.exists(ipath):
            assert safe_rename_file(src=ibak, dst=ipath)
        if not os.path.exists(dpath):
            assert safe_rename_file(src=dbak, dst=dpath)
        assert os.path.isfile(ipath), f"Non-existent index {ipath}"
        assert os.path.isfile(dpath), f"Non-existent datas {dpath}"
        # Check all index keys, remove and restore bad index file
        if os.path.isfile(ibak) and not cls.check_index(ipath, ibak):
            # Restore index
            assert safe_remove_file(ipath)
            assert safe_rename_file(src=ibak, dst=ipath)
        # Check all datas, restore index and datas
        if os.path.isfile(ipath):
            if cls.check_datas(ipath, dpath):
                assert safe_remove_file(ibak)
                assert safe_remove_file(dbak)
            elif os.path.isfile(dbak) and cls.check_datas(ipath, dbak):
                assert safe_remove_file(ibak)
                assert safe_remove_file(dpath)
                assert safe_rename_file(src=dbak, dst=dpath)
        if os.path.isfile(ibak):
            if cls.check_datas(ibak, dpath):
                assert safe_remove_file(dbak)
                assert safe_remove_file(ipath)
                assert safe_rename_file(src=ibak, dst=ipath)
            elif os.path.isfile(dbak) and cls.check_datas(ibak, dbak):
                assert safe_remove_file(ipath)
                assert safe_remove_file(dpath)
                assert safe_rename_file(src=ibak, dst=ipath)
                assert safe_rename_file(src=dbak, dst=dpath)
        # Backups should not exist at this time
        assert not os.path.exists(ibak), f"Index backup {ibak} still exists"
        assert not os.path.exists(dbak), f"Datas backup {dbak} still exists"
        return cls.check_datas(ipath, dpath)

    @classmethod
    def check_index(cls, source: str, backup: str) -> bool:
        try:
            src: ihdl = ihdl(source)
            bak: ihdl = ihdl(backup)
        except Exception:
            return False

        ret: bool = True
        indexs: Set[str] = set()

        for k, v in bak:
            assert isinstance(k, str)
            if v is not None:
                assert isinstance(v, didx)
                indexs.add(k)
            else:
                assert k in indexs
                indexs.remove(k)
        try:
            for k, v in src:
                assert isinstance(k, str)
                assert isinstance(v, didx)
                assert k in indexs
                indexs.remove(k)
        except Exception:
            ret = False

        assert src.close()
        assert bak.close()
        return len(indexs) == 0 if ret is True else False

    @classmethod
    def check_datas(cls, index: str, datas: str) -> bool:
        try:
            idx: ihdl = ihdl(index)
            dat: dhdl = dhdl(datas)
        except Exception:
            return False

        ret: bool = True
        indexs: Dict[str, didx] = {}

        for k, v in idx:
            assert isinstance(k, str)
            if v is None:
                assert k in indexs
                del indexs[k]
                continue
            assert isinstance(v, didx)
            try:
                if not v.verify(dat.load(offset=v.offset, length=v.length)):
                    ret = False
                    break
            except Exception:
                ret = False
                break
            indexs[k] = v

        assert idx.close()
        assert dat.close()
        return ret

    def put(self, key: str, value: bytes) -> bool:
        assert not self.readonly
        assert isinstance(key, str)
        assert isinstance(value, bytes)
        info: didx = didx.new(offset=self.__dhdl.dump(value), value=value)
        self.__dhdl.sync()
        assert isinstance(info, didx)
        self.index[key] = info
        return self.__dump_index(key)

    def get(self, key: str) -> bytes:
        assert isinstance(key, str)
        inf: didx = self.index[key]
        assert isinstance(inf, didx)
        off: int = inf.offset
        len: int = inf.length
        dat = self.__dhdl.load(offset=off, length=len)
        chk: int = inf.calc(dat)
        assert inf.chksum == chk, "Data validation error "\
            f"{key}({self.__dhdl.path}:{off}+{len}) {chk} != {inf.chksum}"
        return dat

    def pop(self, key: str) -> bool:
        assert not self.readonly
        del self.index[key]
        return self.__dump_index(key, True)


class ctrie:
    """
    Caching and persisting radix trees
    """

    MAX_NODES = int(10**3 / 2)  # TODO: OSError: [Errno 24] Too many open files
    MIN_NODES = int(10**2 / 2)

    def __init__(self,
                 path: str = ".",
                 word: Sequence[int] = (2, ),
                 test: testckey = testskey,
                 cacheidx: int = 10**4,
                 cachemax: int = 10**6,
                 readonly: bool = True):
        assert isinstance(path, str)
        assert isinstance(cacheidx, int)
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
        nodes: int = self.__names.nodes
        cacheobj: int = nodes if nodes < self.MAX_NODES else min(
            max(int(nodes / 2), self.MIN_NODES), self.MAX_NODES)
        self.__icache: cache[str, radix] = cache(max(cacheidx, cache.MINIMUM))
        self.__scache: cache[str, store] = cache(max(cacheobj, cache.MINIMUM))
        self.__dcache: cache[str, bytes] = cache(max(cachemax, cache.MINIMUM))
        self.__readonly: bool = readonly
        self.__iter_name: List[str] = []
        self.__iter_curr: Optional[radix[didx]] = None

    def __iter__(self):
        self.__iter_name = [i for i in self.__names]
        if len(self.__iter_name) > 0:
            self.__iter_name.sort(reverse=True)
            self.__iter_curr = iter(self.__route(self.__iter_name.pop()))
        return self

    def __next__(self):
        while self.__iter_curr is not None:
            try:
                return next(self.__iter_curr)
            except StopIteration:
                if len(self.__iter_name) == 0:
                    self.__iter_curr = None
                    continue
                self.__iter_curr = iter(self.__route(self.__iter_name.pop()))
        raise StopIteration

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
                     readonly=self.__readonly,
                     icache=self.__icache)

    def __route(self, key: str) -> store:
        name: str = self.__names.get_name(key)
        stor: store = self.__scache[
            name] if name in self.__scache else self.__get_store(name)
        assert isinstance(stor, store)
        if name not in self.__scache:
            self.__scache[name] = stor
        return stor
