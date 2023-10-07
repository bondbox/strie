# coding:utf-8

from typing import List
from typing import Sequence


def testvkey(key: str) -> bool:
    '''
    allowed characters: 0-9, a-f
    '''

    allowed_char = {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd',
        'e', 'f'
    }

    if not isinstance(key, str):
        return False
    if len(key) % 2 != 0:
        return False
    for i in key:
        if i not in allowed_char:
            return False
    return True


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
    assert testvkey(key=key)
    return key
