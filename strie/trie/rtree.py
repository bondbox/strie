# coding:utf-8

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

from ..utils import testckey

VT = TypeVar("VT")  # Value type.
VTT = TypeVar("VTT")  # Value type.

testskey = testckey(allowed_char=testckey.skey)


class radix(Dict[str, VT]):
    """
    Radix tree
    """

    LEAFS = 128
    NODES = 256

    class store(Dict[str, VTT]):

        def __init__(self, threshold: int):
            assert isinstance(threshold, int) and threshold > 0
            self.__upper: int = min(threshold, radix.LEAFS)
            self.__lower: int = int(threshold / 2)
            self.__stats: List[int] = [0] * radix.NODES
            self.__items: Dict[str, VTT] = {}

        @property
        def stats(self) -> List[int]:
            return self.__stats

        @property
        def lower(self) -> int:
            return self.__lower

        @property
        def upper(self) -> int:
            return self.__upper

        def keys(self) -> List[str]:
            return list(self.__items.keys())

        def __len__(self) -> int:
            return len(self.__items)

        def __iter__(self):
            return iter(self.keys())

        def __contains__(self, key: str) -> bool:
            return key in self.__items

        def __setitem__(self, key: str, value: VTT):
            self.put(key=key, value=value)

        def __getitem__(self, key) -> VTT:
            return self.__items[key]

        def __delitem__(self, key: str):
            if key in self.__items and key != "":
                self.__stats[ord(key[0])] -= 1
            del self.__items[key]

        def put(self, key: str, value: VTT) -> bool:
            split = False
            if key not in self.__items and key != "":
                index = ord(key[0])
                self.__stats[index] += 1
                split = self.__stats[index] >= self.__upper
            self.__items[key] = value
            return split

    def __init__(self,
                 prefix: str = "",
                 test: testckey = testskey,
                 root: Optional["radix"] = None):
        assert isinstance(test, testckey)
        if prefix != "":
            assert isinstance(test, testckey) and test.check(prefix)
        length: int = len(prefix)

        assert (isinstance(root, radix) and length > 0) or root is None
        maximum: int = 1 if root is None else root.__leafs.upper * 2**length

        self.__prefix: str = prefix
        self.__length: int = length
        self.__modify: bool = False
        self.__test: testckey = test
        self.__root: Optional[radix] = root
        self.__tack: bool = True if root is None else False
        self.__leafs: radix.store[VT] = radix.store(threshold=maximum)
        self.__nodes: Dict[str, radix] = {}
        self.__count: int = 0
        self.__iter_objs: List[Tuple[str, radix]] = []
        self.__iter_keys: List[str] = []

    @property
    def name(self) -> str:
        return self.__fullname()

    @property
    def test(self) -> testckey:
        return self.__test

    def nick(self, key: str) -> str:
        return self.__nickname(key)

    @property
    def prefix(self) -> str:
        return self.__prefix

    @prefix.setter
    def prefix(self, value: str):
        assert isinstance(value, str)
        length = len(value)
        assert length > 0
        self.__prefix = value
        self.__length = length

    @property
    def child(self) -> List["radix"]:
        return list(self.__nodes.values())

    @property
    def leafs(self) -> List[str]:
        return self.__leafs.keys()

    @property
    def modify(self) -> bool:
        return self.__modify

    def __fullname(self, end: Optional["radix"] = None) -> str:
        keys: List[str] = []
        curr: Optional[radix] = self
        while curr is not None:
            keys.insert(0, curr.prefix)
            if curr is end:
                break
            curr = curr.__root
        return "".join(keys)

    def __nickname(self, key: str) -> str:
        assert isinstance(key, str)
        assert len(key) >= self.__length
        assert key[:self.__length] == self.prefix
        return key[self.__length:]

    def __check(self, key: str) -> bool:
        return key[:self.__length] == self.prefix

    def __len__(self) -> int:
        return self.__count

    def __iter__(self):
        return self.__iter_init()

    def __next__(self) -> str:
        return self.__iter_walk()

    def __contains__(self, key: str) -> bool:
        assert isinstance(key, str)
        obj: radix[VT] = self
        while True:
            assert obj.__check(key)
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)
            if isinstance(tmp, radix):
                obj = tmp
                continue
            return key in obj.__leafs

    def __setitem__(self, key: str, value: VT):
        assert self.put(key=key, value=value, modify=True)

    def __getitem__(self, key: str) -> VT:
        return self.get(key=key)

    def __delitem__(self, key: str):
        assert self.pop(key=key)

    def __chg(self) -> bool:
        curr: Optional[radix] = self
        while curr is not None:
            if curr.__modify is True:
                break
            curr.__modify = True
            curr = curr.__root
        return True

    def __inc(self, v: int = 1) -> int:
        assert isinstance(v, int) and v > 0
        curr: Optional[radix] = self
        while curr is not None:
            curr.__count += v
            curr = curr.__root
        return v

    def __dec(self, v: int = 1) -> int:
        assert isinstance(v, int) and v > 0
        curr: Optional[radix] = self
        prev = None
        while curr is not None:
            curr.__count -= v
            assert curr.__count >= 0
            if prev is not None:
                if prev.__tack is False:
                    # recycle child node with fewer leaves
                    if prev.__count <= curr.__leafs.lower:
                        for key in prev:
                            assert key not in curr.__leafs
                            curr.__leafs[key] = prev[key]
                        prev.__count = 0
                    # trim empty child node
                    if prev.__count == 0:
                        assert curr.__get_node(prev.prefix) is prev
                        assert curr.__del_node(prev.prefix)
            prev = curr
            curr = curr.__root
        return v

    def __iter_init(self):
        '''
        DFS(Depth First Search) initialization
        '''
        assert isinstance(self.__iter_keys, List)
        assert isinstance(self.__iter_objs, List)

        prev = [self]
        self.__iter_keys.clear()
        self.__iter_objs.clear()

        while len(prev) > 0:
            curr = []
            for node in prev:
                name = node.__fullname(end=self)
                self.__iter_objs.append((name, node))
                curr.extend(node.child)
            prev = curr

        return self

    def __iter_walk(self) -> str:
        '''
        DFS(Depth First Search) iteration
        '''

        while True:
            if len(self.__iter_keys) > 0:
                return self.__iter_keys.pop()

            if len(self.__iter_objs) > 0:
                name, node = self.__iter_objs.pop()
                self.__iter_keys.extend([name + k for k in node.leafs])
                continue

            raise StopIteration

    def __split_node(self, key: str, modify: bool = True):
        '''
        split new node
        '''
        prefix = key[0]
        obj: radix[VT] = self

        def recheck(curr: radix):
            while curr.__root is not None and not curr.__root.__tack:
                prev = curr
                curr = curr.__root
                assert curr.__get_node(prev.prefix) is prev
                if len(prev.__leafs) > 0:
                    continue
                if len(prev.__nodes) > 1:
                    continue
                assert len(prev.__leafs) == 0
                assert len(prev.__nodes) == 1
                node, = prev.__nodes.values()
                node.prefix = prev.prefix + node.prefix
                assert node.prefix not in curr.__nodes
                assert curr.__set_node(value=node, modify=modify)
                assert curr.__del_node(prev.prefix)

        while True:
            assert obj.__get_node(prefix) is None

            newobj: radix[VT] = radix(prefix=prefix, root=obj)
            obj.__set_node(value=newobj, modify=modify)

            for i in range(radix.NODES + 1):
                if i >= radix.NODES:
                    recheck(curr=newobj)
                    return
                if newobj.__leafs.stats[i] >= newobj.__leafs.upper:
                    prefix = chr(i)
                    obj = newobj
                    break

    def __set_node(self, value: "radix", modify: bool = True) -> bool:
        assert isinstance(value, radix) and len(value.prefix) > 0
        assert value.prefix not in self.__nodes
        assert isinstance(modify, bool)
        # check root node
        if value.__root is not self:
            value.__root = self
        # add child leafs
        for key in self.__leafs:
            if key[:value.__length] == value.prefix:
                newkey = key[value.__length:]
                assert newkey not in value.__leafs
                value.__leafs[newkey] = self.__leafs[key]
                value.__count += 1
                del self.__leafs[key]
                if modify is True:
                    assert value.__chg() is True
        # add child nodes
        for key in list(self.__nodes.keys()):
            if key[:value.__length] == value.prefix:
                newkey = key[value.__length:]
                self.__nodes[key].__root = value
                self.__nodes[key].prefix = newkey
                value.__count += len(self.__nodes[key])
                value.__nodes[newkey] = self.__nodes[key]
                del self.__nodes[key]
        self.__nodes[value.prefix] = value
        return True

    def __get_node(self, prefix: str) -> Optional["radix"]:
        assert isinstance(prefix, str)
        head = 1
        tail = len(prefix)
        while tail >= head:
            if prefix[:tail] in self.__nodes:
                return self.__nodes[prefix[:tail]]
            tail -= 1
            if prefix[:head] in self.__nodes:
                return self.__nodes[prefix[:head]]
            head += 1
        return None

    def __del_node(self, prefix: str) -> bool:
        assert isinstance(prefix, str) and len(prefix) > 0
        assert prefix in self.__nodes and self.__nodes[prefix].__tack is False
        del self.__nodes[prefix]
        return True

    def pin(self, prefix: str) -> bool:
        assert isinstance(prefix, str) and len(prefix) > 0
        obj = radix(prefix=prefix, root=self)
        obj.__tack = True
        tmp = self
        while tmp is not None:
            assert tmp.__tack is True
            tmp = tmp.__root
        return self.__set_node(obj)

    def put(self, key: str, value: VT, modify: bool = True) -> bool:
        assert self.__test.check(key) and self.__check(key)
        assert isinstance(modify, bool)

        obj: radix[VT] = self

        while True:
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)

            # search child node
            if isinstance(tmp, radix):
                obj = tmp
                continue

            # count inc if key not exist
            if key in obj.__leafs:
                assert modify is True
            else:
                assert obj.__inc() == 1

            # mark node leaf modify
            if modify is True:
                assert obj.__chg() is True

            if obj.__leafs.put(key=key, value=value):
                obj.__split_node(key=key, modify=modify)
            return True

    def get(self, key: str) -> VT:
        assert isinstance(key, str)
        obj: radix[VT] = self
        while True:
            assert obj.__check(key)
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)
            if isinstance(tmp, radix):
                obj = tmp
                continue
            return obj.__leafs[key]

    def pop(self, key: str) -> bool:
        assert isinstance(key, str) and self.__check(key)
        obj: radix[VT] = self

        while True:
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)

            # search child node
            if isinstance(tmp, radix):
                obj = tmp
                continue

            # failure if key not exist
            if key not in obj.__leafs:
                return False

            # delete leaf and mark node leaf modify
            assert obj.__chg() is True
            del obj.__leafs[key]
            assert obj.__dec() == 1
            return True

    def trim(self, key: str) -> int:
        assert isinstance(key, str)
        obj: radix[VT] = self
        sum: int = 0

        while len(key) >= 0:
            assert obj.__check(key)
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)
            # search child node
            if isinstance(tmp, radix):
                assert len(tmp) > 0
                assert len(obj) >= len(tmp)
                # continue if key not empty
                if len(tmp.__nickname(key)) > 0:
                    obj = tmp
                    continue
                # delete endpoint and recount
                assert obj.__del_node(tmp.prefix)
                return obj.__dec(len(tmp))
            sumdec: int = 0
            length: int = len(key)
            delete: List[str] = []
            for k in obj.__nodes:
                if k[:length] == key:
                    delete.append(k)
            for k in delete:
                sumdec += len(obj.__nodes[k])
                assert obj.__del_node(k)
            if sumdec > 0:
                sum += obj.__dec(sumdec)
            break

        sumdec: int = 0
        length: int = len(key)
        delete: List[str] = []
        for k in obj.__leafs:
            if k[:length] == key:
                delete.append(k)
        for k in delete:
            assert k in obj.__leafs
            del obj.__leafs[k]
            assert k not in obj.__leafs
            sumdec += 1

        if sumdec > 0:
            sum += obj.__dec(sumdec)
        return sum
