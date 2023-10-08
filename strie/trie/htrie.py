# coding:utf-8

from .radix import radix


def testhkey(key: str) -> bool:
    '''
    allowed characters: 0-9, a-f
    '''

    allowed_char = {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd',
        'e', 'f'
    }

    if not isinstance(key, str):
        return False
    if len(key) < 2 and key != "":
        return False
    for i in key:
        if i not in allowed_char:
            return False
    return True


def htrie(prefix: str = "") -> radix:
    """
    Hash-based radix tree
    """
    root = radix(prefix=prefix, test=testhkey)
    for i in range(256):
        root.pin(prefix=f"{i:02x}")
    return root
