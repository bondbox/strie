# coding:utf-8

import os
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..trie import ctrie
from ..utils import URL_PROG
from ..utils import __prog_del__
from ..utils import __version__
from .arg import add_keys
from .arg import add_path


@add_command("pop")
def add_cmd(_arg: argp):
    add_path(_arg)
    add_keys(_arg)


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    assert os.path.isdir(cmds.args.path), f"Non-existent dir {cmds.args.path}"
    root = ctrie(path=cmds.args.path, readonly=False)
    for key in cmds.args.keys:
        if key in root:
            # value = root[key]
            del root[key]
            cmds.stdout(f"Deleted {key}.")
        else:
            cmds.stderr(f"Non-existent {key}.")
        assert key not in root
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_del__,
                    description="String trie command line.",
                    epilog=f"For more, please visit {URL_PROG}.")
