# -*- coding:utf-8 -*-
import re
import inspect
import logging
import sys
import argparse
from handofcats.compat import write
from handofcats.parsercreator import ParserCreator
from handofcats.commandcreator import CommandFromFunction
from handofcats.middlewares import MiddlewareApplicator
from handofcats.commandcollector import CommandCollector
logger = logging.getLogger(__name__)

# default collector
COLLECTOR = CommandCollector()


def get_help_dict(doc):
    d = {}
    rx = re.compile("^ *:param +(?P<param>\w+): +(?P<doc>.+) *$", re.M)
    d.update({name: doc for name, doc in rx.findall(doc)})
    rx = re.compile("^ *:param +(?P<type>\w+) +(?P<param>\w+): +(?P<doc>.+) *$", re.M)
    d.update({name: doc for type_, name, doc in rx.findall(doc)})
    return d


def get_description(doc):
    r = []
    for line in doc.split("\n"):
        line = line.strip()
        if line and not line.startswith(":"):
            r.append(line)
    return "\n".join(r)


def as_command(fn=None, middlewares=None):
    def call(fn, level=2):
        argspec = inspect.getargspec(fn)
        doc = fn.__doc__ or ""
        help_dict = get_help_dict(doc)
        description = get_description(doc)

        if middlewares:
            middleware_applicator = MiddlewareApplicator(middlewares)
        else:
            middleware_applicator = None

        parser_creator = ParserCreator(argspec, help_dict, description)

        caller = CommandFromFunction(
            fn,
            parser_creator=parser_creator,
            middleware_applicator=middleware_applicator,
            mark=COLLECTOR.mark
        )
        return caller.activate(level=level)

    if fn is None:
        return call
    else:
        return call(fn, level=3)


def describe(usage="command:\n", out=sys.stdout, package=None, name=None, level=1, scan=COLLECTOR.scan):
    if name is None:
        frame = sys._getframe(level)
        name = frame.f_globals["__name__"]
        package = frame.f_globals["__package__"]

    if name == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--full", default=False, action="store_true", dest="full_description")
        args = parser.parse_args(sys.argv[1:])
        commands = list(sorted(scan(package), key=lambda x: x.name))

        write(out, "avaiable commands are here. (with --full option, showing full text)\n\n")
        for command in commands:
            if command.short_description:
                write(out, u"- {} -- {}\n".format(command.name, command.short_description))
            else:
                write(out, u"- {}\n".format(command.name))

        if args.full_description and commands:
            write(out, u"\n")
            for command in commands:
                write(out, u"\n---{}-------------------------------------\n".format(command.name))
                command.print_help(out)

# alias
handofcats = as_command
