# coding:utf-8

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .utils import testkey


class radix:

    LEAFS = 8
    NODES = 256

    def __init__(self, prefix: str = "", threshold: int = 16):
        assert isinstance(threshold, int) and threshold >= radix.LEAFS
        assert testkey(key=prefix)
        self.__prefix: str = prefix
        self.__length: int = len(prefix)
        self.__modify: bool = False
        self.__thold: int = threshold
        self.__nodes: List[Optional[radix]] = [None] * radix.NODES
        self.__stats: List[int] = [0] * radix.NODES
        self.__leafs: Dict[str, Any] = {}
        self.__count: int = 0
        self.__iter_name: str = ""
        self.__iter_curr: radix = self
        self.__iter_prev: radix = self
        self.__iter_keys: List[str] = []
        self.__iter_objs: List[radix] = []

    @property
    def child(self) -> List["radix"]:
        return [i for i in self.__nodes if isinstance(i, radix)]

    @property
    def modify(self) -> bool:
        return self.__modify

    def __nickname(self, key: str) -> str:
        assert isinstance(key, str)
        assert len(key) >= self.__length
        assert key[:self.__length] == self.__prefix
        return key[self.__length:]

    def __check(self, key: str) -> bool:
        return key[:self.__length] == self.__prefix

    def __index(self, key: str) -> int:
        index = key[self.__length:self.__length + 2]
        return int(index, 16) if index != "" else -1

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
            idx = obj.__index(key)
            key = obj.__nickname(key)
            tmp = obj.__nodes[idx] if idx >= 0 else None
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
        prefix: str = prev.__iter_name
        tmp: radix = prev
        obj: radix = self
        while True:
            prefix += obj.__prefix
            obj.__iter_name = prefix
            obj.__iter_curr = obj
            obj.__iter_prev = tmp
            obj.__iter_keys = list(obj.__leafs.keys())
            obj.__iter_objs = [i for i in obj.__nodes if isinstance(i, radix)]

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
        obj: radix = self.__iter_curr
        while True:
            if obj.__iter_curr is obj:
                # Return this node after all child nodes
                if len(obj.__iter_keys) > 0:
                    # For quick next time
                    if self.__iter_curr is not obj:
                        self.__iter_curr = obj
                    # Return the fullname
                    return obj.__iter_name + obj.__iter_keys.pop()

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

    def __node_split(self, index: int):
        '''
        split new node
        '''
        obj: radix = self
        while True:
            assert index >= 0 and index < radix.NODES
            assert obj.__nodes[index] is None

            prefix: str = f"{index:02x}"
            newobj: radix = radix(prefix=prefix, threshold=self.__thold)
            for k, v in obj.__leafs.items():
                if k[:2] == prefix:
                    newobj.__leafs[k[2:]] = v
                    newobj.__count += 1
                    newkey = k[2:4]
                    if newkey != "":
                        newobj.__stats[int(newkey, 16)] += 1
            assert obj.__stats[index] == len(newobj)
            for i in newobj:
                del obj.__leafs[i]
                obj.__stats[index] -= 1
            assert obj.__stats[index] == 0
            obj.__nodes[index] = newobj
            for i in range(radix.NODES + 1):
                if i >= radix.NODES:
                    return
                if newobj.__stats[i] >= obj.__thold:
                    obj = newobj
                    index = i
                    break

    def put(self, key: str, value: Any, modify: bool = True) -> bool:
        assert testkey(key=key) and self.__check(key)
        assert isinstance(modify, bool)

        obj: radix = self
        stk: List[radix] = []

        def stack_inc():
            while len(stk) > 0:
                stk.pop().__count += 1

        while True:
            stk.append(obj)
            idx = obj.__index(key)
            key = obj.__nickname(key)
            tmp = obj.__nodes[idx] if idx >= 0 else None

            # search child node
            if isinstance(tmp, radix):
                obj = tmp
                continue

            # count inc if key not exist
            if key in obj.__leafs:
                assert modify is True
            else:
                stack_inc()
                if idx >= 0:
                    obj.__stats[idx] += 1

            # mark node leaf modify
            if modify is True:
                obj.__modify = True

            obj.__leafs[key] = value
            if obj.__stats[idx] >= obj.__thold:
                obj.__node_split(index=idx)
            return True

    def get(self, key: str) -> Any:
        assert isinstance(key, str)
        obj: radix = self
        while True:
            if not obj.__check(key):
                return None
            idx = obj.__index(key)
            key = obj.__nickname(key)
            tmp = obj.__nodes[idx] if idx >= 0 else None
            if isinstance(tmp, radix):
                obj = tmp
                continue
            return obj.__leafs[key]

    def pop(self, key: str) -> bool:
        assert isinstance(key, str) and self.__check(key)
        stk: List[radix] = []
        obj: radix = self

        def stack_dec():
            while len(stk) > 0:
                stk.pop().__count -= 1

        while True:
            stk.append(obj)
            idx = obj.__index(key)
            key = obj.__nickname(key)
            tmp = obj.__nodes[idx] if idx >= 0 else None

            # search child node
            if isinstance(tmp, radix):
                if len(tmp) == 1:
                    # delete empty node
                    obj.__nodes[idx] = None
                    if idx >= 0:
                        obj.__stats[idx] -= 1
                    stack_dec()
                    return True
                obj = tmp
                continue

            # failure if key not exist
            if key not in obj.__leafs:
                return False

            # delete leaf and mark node leaf modify
            obj.__modify = True
            del obj.__leafs[key]
            stack_dec()
            return True

    def trim(self, key: str) -> bool:
        assert isinstance(key, str)
        stk: List[radix] = []
        obj: radix = self

        def stack_recount(dec: int):
            assert isinstance(dec, int) and dec > 0
            while len(stk) > 0:
                stk.pop().__count -= dec

        while len(key) > 0:
            assert obj.__check(key)
            stk.append(obj)
            idx = obj.__index(key)
            key = obj.__nickname(key)
            tmp = obj.__nodes[idx] if idx >= 0 else None
            # search child node
            if isinstance(tmp, radix):
                # continue if key not empty
                if len(tmp.__nickname(key)) > 0:
                    obj = tmp
                    continue
                # delete endpoint and recount
                obj.__nodes[idx] = None
                stack_recount(len(tmp))
                return True
            # not find child node
            break

        # failure if key not exist
        if key not in obj.__leafs:
            return False

        # delete leaf and recount
        del obj.__leafs[key]
        # assert obj in stk
        stack_recount(1)
        return True
