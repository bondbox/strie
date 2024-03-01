# coding:utf-8

import os
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..trie import ctrie
from ..utils import __prog_set__
from ..utils import __url_home__
from ..utils import __version__
from .arg import add_encode
from .arg import add_path


@add_command("set")
def add_cmd(_arg: argp):
    add_path(_arg)
    add_encode(_arg)
    _arg.add_pos("key", type=str, nargs=1, metavar="KEY")
    _arg.add_pos("val", type=str, nargs=1, metavar="VALUE")


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    assert os.path.isdir(cmds.args.path), f"Non-existent dir {cmds.args.path}"
    root = ctrie(path=cmds.args.path, readonly=False)
    key: str = cmds.args.key[0]
    val: str = cmds.args.val[0]
    assert isinstance(key, str), f"unexpected type: {type(key)}"
    assert isinstance(val, str), f"unexpected type: {type(val)}"
    root[key] = val.encode(cmds.args.encode)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_set__,
                    description="String trie command line.",
                    epilog=f"For more, please visit {__url_home__}.")
