# coding:utf-8

from typing import Callable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Union


class testckey:
    '''
    check visual key
    '''

    MAX_CHARACTERS: int = 65536
    """
    hash keys allowed characters: 0-9, a-f
    """
    hkey: Set[str] = {
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d",
        "e", "f"
    }
    """
    string keys allowed characters: 0-9, A-Z, a-z

    for i in range(ord("0"), ord("9") + 1):
        print(f"'{chr(i)}',")

    for i in range(ord("A"), ord("Z") + 1):
        print(f"'{chr(i)}',")

    for i in range(ord("a"), ord("z") + 1):
        print(f"'{chr(i)}',")
    """
    skey: Set[str] = {
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D",
        "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
        "S", "T", "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f",
        "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
        "u", "v", "w", "x", "y", "z"
    }

    def __init__(self,
                 length_limit: int = MAX_CHARACTERS,
                 allowed_char: Union[Sequence[str], Set[str]] = skey,
                 inspection: Optional[Callable[[str, int], bool]] = None):
        assert isinstance(length_limit, int) and length_limit > 0
        assert length_limit <= self.MAX_CHARACTERS
        self.__lim: int = length_limit
        self.__set: Set[str] = {c for c in allowed_char if len(c) == 1}
        self.__chk: Optional[Callable[[str, int], bool]] = inspection

    @property
    def characters(self) -> Set[str]:
        return self.__set

    def check(self, key: str) -> bool:
        if not isinstance(key, str):
            return False
        length = len(key)
        if length <= 0 or length > self.__lim:
            return False
        for k in key:
            if k not in self.characters:
                return False
        return True if self.__chk is None else self.__chk(key, length)


def checkvkey(key: str, len: int) -> bool:
    if len % 2 != 0:
        return False
    return True


testvkey = testckey(allowed_char=testckey.hkey, inspection=checkvkey)


def seqtokey(datas: Sequence[int], reverse: bool = False):
    assert isinstance(datas, Sequence)
    assert isinstance(reverse, bool)
    res: List[str] = []
    for i in datas:
        assert isinstance(i, int)
        assert i >= 0 and i <= 255
        res.append(f"{i:02x}")
    if reverse:
        res.reverse()
    key = "".join(res).lower()
    assert testvkey.check(key)
    return key
