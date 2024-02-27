# coding:utf-8

import os
from typing import List
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..trie import ctrie
from ..utils import __prog_list__
from ..utils import __url_home__
from ..utils import __version__
from .arg import add_decode
from .arg import add_path


@add_command("list")
def add_cmd(_arg: argp):
    add_path(_arg)
    def_csize: int = 10**5
    _arg.add_argument("--cachesize",
                      type=int,
                      nargs="?",
                      const=def_csize,
                      default=def_csize,
                      metavar="SIZE",
                      help=f"Specify cache max size, default is {def_csize}")
    _arg.add_opt_on("--value", help="Output key and value, default only key")
    _arg.add_opt_on("--count", help="Output count starting from 1")
    add_decode(_arg)


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    assert os.path.isdir(cmds.args.path), f"Non-existent dir {cmds.args.path}"

    root = ctrie(path=cmds.args.path,
                 cachemax=cmds.args.cachesize,
                 readonly=True)

    count: int = 0
    for key in root:
        count += 1
        items: List[str] = []
        if cmds.args.count:
            items.append(str(count))
        items.append(key)
        if cmds.args.value:
            value: bytes = root[key]
            if cmds.args.decode is not None:
                items.append(value.decode(cmds.args.decode))
            else:
                items.append(str(root[key]))
        cmds.stdout(" ".join(items))

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_list__,
                    description="String trie command line.",
                    epilog=f"For more, please visit {__url_home__}.")
