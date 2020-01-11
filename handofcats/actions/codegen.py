import typing as t
import sys
import re
import inspect
import logging
import tempfile
from prestring.naming import titleize
from ..types import TargetFunction, ArgumentParser, SetupParserFunction
from ._codeobject import Module

logger = logging.getLogger(__name__)


def emit(
    m: Module, fn: TargetFunction, *, inplace: bool = False,
):
    import pathlib

    target_file = inspect.getsourcefile(fn)
    source = pathlib.Path(target_file).read_text()
    rx = re.compile(
        r"(?:^@([\S]+\.)?as_command.*|^.*import as_command.*)\n", re.MULTILINE
    )
    exposed = rx.sub("", "".join(source))

    def _dump(out):
        print(exposed, file=out)
        print(m, file=out)

    if not inplace:
        return _dump(sys.stdout)

    outpath = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=".", delete=False) as wf:
            outpath = pathlib.Path(wf.name)
            _dump(wf)

        # create directory
        pathlib.Path(target_file).parent.mkdir(exist_ok=True)
        return outpath.rename(target_file)
    except Exception as e:
        logger.warn("error is occured. rollback (exception=%r)", e)
        pathlib.Path(target_file).write_text(source)
    finally:
        if outpath and outpath.exists():
            outpath.unlink(missing_ok=True)
    sys.exit(1)


def main_code(
    m: Module, fn: t.Callable, *, outname: str = "main", typed: bool = False,
) -> t.Tuple[Module, ArgumentParser]:

    if fn.__name__ == outname:
        outname = titleize(outname)  # main -> Main

    if typed:
        m.sep()
        m.from_("typing").import_("Optional, List  # noqa: E402")
        m.sep()
        mdef = m.def_(outname, "argv: Optional[List[str]] = None", return_type="None")
    else:
        mdef = m.def_(outname, "argv=None")

    with mdef:
        argparse = m.import_("argparse")
        m.sep()
        parser = m.let(
            "parser",
            argparse.ArgumentParser(
                prog=m.getattr(m.symbol(fn), "__name__"),
                description=m.getattr(m.symbol(fn), "__doc__"),
            ),
        )
        m.setattr(parser, "print_usage", parser.print_help)

        m.sep()
        sm = m.submodule()
        m.sep()

        args = m.let("args", parser.parse_args(m.symbol("argv")))
        _ = m.let("params", m.symbol("vars")(args).copy())
        m.return_(f"{fn.__name__}(**params)")

    with m.if_("__name__ == '__main__'"):
        m.stmt(f"{outname}()")
    return sm, parser


def setup_module() -> Module:
    m = Module()
    m.toplevel = m.submodule()
    return m


def run_as_single_command(
    setup_parser: SetupParserFunction,
    fn: TargetFunction,
    argv: t.Optional[str] = None,
    *,
    outname: str = "main",
    inplace: bool = False,
    typed: bool = False,
) -> None:
    """ generate main() code

    something like

    ```
    def main(argv=None):
        import argparse

        parser = argparse.ArgumentParser(prog=hello.__name__, description=hello.__doc__)
        parser.print_usage = parser.print_help

        # adding code, by self.setup_parser(). e.g.
        # parser.add_argument('--name', required=False, default='world', help="(default: 'world')")
        # parser.add_argument('--debug', action="store_true")

        args = parser.parse_args(argv)
        params = vars(args).copy()
        return hello(**params)

    if __name__ == "__main__":
        main()
    ```
    """

    m = Module()
    m.toplevel = m.submodule()

    if fn.__name__ == outname:
        outname = titleize(outname)  # main -> Main

    if typed:
        m.sep()
        m.from_("typing").import_("Optional, List  # noqa: E402")
        m.sep()
        mdef = m.def_(outname, "argv: Optional[List[str]] = None", return_type="None")
    else:
        mdef = m.def_(outname, "argv=None")

    # def main(argv=None):
    with mdef:
        parser, _ = setup_parser(m, fn, customizations=[])

        # args = parser.parse_args(argv)
        args = m.let("args", parser.parse_args(m.symbol("argv")))

        # params = vars(args).copy()
        _ = m.let("params", m.symbol("vars")(args).copy())

        # return fn(**params)
        m.return_(f"{fn.__name__}(**params)")

    # if __name__ == "__main__":
    with m.if_("__name__ == '__main__'"):
        # main()
        m.stmt(f"{outname}()")

    emit(m, fn, inplace=inplace)
