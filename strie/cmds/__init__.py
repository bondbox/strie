# coding:utf-8

from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import __prog__
from ..utils import __url_home__
from ..utils import __version__
from .get import add_cmd as add_cmd_get
from .init import add_cmd as add_cmd_init
from .list import add_cmd as add_cmd_list
from .pop import add_cmd as add_cmd_del
from .set import add_cmd as add_cmd_set


@add_command(__prog__)
def add_cmd(_arg: argp):
    pass


@run_command(add_cmd, add_cmd_init, add_cmd_list, add_cmd_set, add_cmd_get,
             add_cmd_del)
def run_cmd(cmds: commands) -> int:
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog__,
                    description="String trie command line.",
                    epilog=f"For more, please visit {__url_home__}.")
