# coding:utf-8

from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..trie import ctrie
from ..utils import __prog_init__
from ..utils import __url_home__
from ..utils import __version__
from ..utils import testakey
from .arg import add_path


@add_command("init")
def add_cmd(_arg: argp):
    add_path(_arg)

    _arg.add_argument("-w",
                      "--word",
                      type=int,
                      nargs=1,
                      dest="word",
                      metavar="LEN",
                      action="extend",
                      help="Character split length")

    group = _arg.argument_group("characters")
    mgroup = group.add_mutually_exclusive_group()
    mgroup.add_argument("--hex",
                        dest="keys",
                        const=testakey.hex,
                        action="store_const",
                        help="hex keys allowed characters: 0-9, a-f")
    mgroup.add_argument(
        "--alnum",
        dest="keys",
        const=testakey.alnum,
        action="store_const",
        help="alpha-numeric keys allowed characters: 0-9, A-Z, a-z")
    mgroup.add_argument("-k",
                        "--key",
                        type=str,
                        nargs=1,
                        dest="keys",
                        metavar="CHAR",
                        action="extend",
                        help="Allowed characters, default is alpha-numeric")


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    assert cmds.args.word is not None, "Please specify split length"
    if cmds.args.keys is None:
        cmds.args.keys = testakey.alnum
    cmds.args.test = testakey(allowed_char=cmds.args.keys)
    assert ctrie.init(path=cmds.args.path,
                      word=cmds.args.word,
                      test=cmds.args.test)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_init__,
                    description="String trie command line.",
                    epilog=f"For more, please visit {__url_home__}.")
