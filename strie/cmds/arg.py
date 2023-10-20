# coding:utf-8

from xarg import argp


def add_path(_arg: argp):
    _arg.add_argument("-p",
                      "--path",
                      type=str,
                      nargs="?",
                      const=".",
                      default=".",
                      metavar="DIR",
                      help="Specify directory")


def add_keys(_arg: argp):
    _arg.add_pos("keys", type=str, nargs="+", metavar="KEY")


def add_decode(_arg: argp):
    _arg.add_argument("--decode",
                      type=str,
                      nargs="?",
                      const="utf-8",
                      default=None,
                      metavar="CODING",
                      choices=["utf-8"],
                      help="Output decoding string")


def add_encode(_arg: argp):
    _arg.add_argument("--encode",
                      type=str,
                      nargs="?",
                      const="utf-8",
                      default="utf-8",
                      metavar="CODING",
                      choices=["utf-8"],
                      help="Encoding output string")
