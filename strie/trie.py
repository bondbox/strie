# coding:utf-8

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .utils import testkey


class radix:

    LEAFS = 128
    NODES = 256

    class store:

        def __init__(self, threshold: int):
            assert isinstance(threshold, int) and threshold > 0
            self.__upper: int = min(threshold, radix.LEAFS)
            self.__lower: int = int(threshold / 2)
            self.__stats: List[int] = [0] * radix.NODES
            self.__items: Dict[str, Any] = {}

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

        def __setitem__(self, key: str, value: Any):
            self.put(key=key, value=value)

        def __getitem__(self, key: str) -> Any:
            return self.__items[key]

        def __delitem__(self, key: str):
            if key in self.__items and key != "":
                self.__stats[int(key[:2], 16)] -= 1
            del self.__items[key]

        def put(self, key: str, value: Any) -> bool:
            index = int(key[:2], 16)
            if key not in self.__items and key != "":
                self.__stats[index] += 1
            self.__items[key] = value
            return self.__stats[index] >= self.__upper

    def __init__(self, prefix: str = "", root: Optional["radix"] = None):
        assert testkey(key=prefix)
        assert (isinstance(root, radix) and len(prefix) > 0) or root is None
        threshold = root.__leafs.upper * 2 if isinstance(root, radix) else 1
        self.__root: Optional[radix] = root
        self.__prefix: str = prefix
        self.__length: int = len(prefix)
        self.__modify: bool = False
        self.__leafs: radix.store = radix.store(threshold)
        self.__nodes: Dict[str, radix] = {}
        self.__count: int = 0
        self.__iter_curr: radix = self
        self.__iter_prev: radix = self
        self.__iter_keys: List[str] = []
        self.__iter_objs: List[radix] = []

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
    def leafs(self) -> List[Any]:
        return self.__leafs.keys()

    @property
    def modify(self) -> bool:
        return self.__modify

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
        return self.__iter_init(prev=self)

    def __next__(self) -> str:
        return self.__iter_walk()

    def __contains__(self, key: str) -> bool:
        assert isinstance(key, str)
        obj: radix = self
        while True:
            if not obj.__check(key):
                return False
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)
            if isinstance(tmp, radix):
                obj = tmp
                continue
            return key in obj.__leafs

    def __setitem__(self, key: str, value: Any):
        self.put(key=key, value=value, modify=True)

    def __getitem__(self, key: str) -> Any:
        return self.get(key=key)

    def __delitem__(self, key: str):
        self.pop(key=key)

    def __iter_init(self, prev: "radix"):
        '''
        DFS(Depth First Search) initialization
        '''
        tmp: radix = prev
        obj: radix = self
        while True:
            obj.__iter_curr = obj
            obj.__iter_prev = tmp
            obj.__iter_keys = obj.leafs
            obj.__iter_objs = obj.child

            if len(obj.__iter_objs) <= 0:
                self.__iter_curr = obj
                return self

            obj.__iter_curr = obj.__iter_objs.pop()
            tmp = obj
            obj = obj.__iter_curr

    def __iter_walk(self) -> str:
        '''
        DFS(Depth First Search) iteration
        '''

        def fullname(curr: radix, key: str) -> str:
            keys: List[str] = [key]
            while curr.__iter_prev is not curr:
                keys.insert(0, curr.prefix)
                curr = curr.__iter_prev
            keys.insert(0, curr.prefix)
            return "".join(keys)

        obj: radix = self.__iter_curr
        while True:
            if obj.__iter_curr is obj:
                # Return this node after all child nodes
                if len(obj.__iter_keys) > 0:
                    # For quick next time
                    if self.__iter_curr is not obj:
                        self.__iter_curr = obj
                    # Return the fullname
                    return fullname(curr=obj, key=obj.__iter_keys.pop())

                # The root node stops iteration
                if obj.__iter_prev is obj:
                    raise StopIteration

                # Back to previous node
                obj = obj.__iter_prev
                continue

            # No child nodes, next itself
            if len(obj.__iter_objs) <= 0:
                obj.__iter_curr = obj
                continue

            # Next child node
            tmp = obj.__iter_objs.pop()
            tmp.__iter_init(prev=obj)
            obj = tmp.__iter_curr

    def __split_node(self, key: str, modify: bool):
        '''
        split new node
        '''
        prefix = key[:2]
        obj: radix = self

        def recheck(curr: radix):
            while curr.__root is not None:
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

            newobj: radix = radix(prefix=prefix, root=obj)
            obj.__set_node(value=newobj, modify=modify)

            for i in range(radix.NODES + 1):
                if i >= radix.NODES:
                    recheck(curr=newobj)
                    return
                if newobj.__leafs.stats[i] >= newobj.__leafs.upper:
                    obj = newobj
                    prefix = f"{i:02x}"
                    break

    def __set_node(self, value: "radix", modify: bool) -> bool:
        assert isinstance(value, radix) and len(value.prefix) > 0
        assert value.prefix not in self.__nodes
        assert isinstance(modify, bool)
        value.__root = self
        for key in self.__leafs:
            if key[:value.__length] == value.prefix:
                newkey = key[value.__length:]
                assert newkey not in value.__leafs
                value.__leafs[newkey] = self.__leafs[key]
                value.__count += 1
                del self.__leafs[key]
                if modify is True:
                    self.__modify = True
                    value.__modify = True
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
        assert prefix in self.__nodes
        del self.__nodes[prefix]
        return True

    def put(self, key: str, value: Any, modify: bool = True) -> bool:
        assert testkey(key=key) and self.__check(key)
        assert isinstance(modify, bool)

        obj: radix = self

        def inc(curr: Optional[radix]):
            assert isinstance(curr, radix)
            while curr is not None:
                curr.__count += 1
                curr = curr.__root

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
                inc(curr=obj)

            # mark node leaf modify
            if modify is True:
                obj.__modify = True

            if obj.__leafs.put(key=key, value=value):
                obj.__split_node(key=key, modify=modify)
            return True

    def get(self, key: str) -> Any:
        assert isinstance(key, str)
        obj: radix = self
        while True:
            if not obj.__check(key):
                return None
            key = obj.__nickname(key)
            tmp = obj.__get_node(key)
            if isinstance(tmp, radix):
                obj = tmp
                continue
            return obj.__leafs[key]

    def pop(self, key: str) -> bool:
        assert isinstance(key, str) and self.__check(key)
        obj: radix = self

        def dec(curr: Optional[radix]):
            assert isinstance(curr, radix)
            prev = None
            while curr is not None:
                curr.__count -= 1
                assert curr.__count >= 0
                if prev is not None:
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
            obj.__modify = True
            del obj.__leafs[key]
            dec(curr=obj)
            return True

    def trim(self, key: str) -> int:
        assert isinstance(key, str)
        obj: radix = self
        sum: int = 0

        def recount(curr: Optional[radix], dec: int) -> int:
            assert isinstance(curr, radix)
            assert isinstance(dec, int) and dec > 0
            prev = None
            while curr is not None:
                curr.__count -= dec
                assert curr.__count >= 0
                if prev is not None:
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
            return dec

        while len(key) > 0:
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
                return recount(curr=obj, dec=len(tmp))
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
                sum += recount(curr=obj, dec=sumdec)
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
            sum += recount(curr=obj, dec=sumdec)
        return sum
