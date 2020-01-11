import typing as t
import sys
import re
import inspect
import logging
import tempfile
import pathlib
from prestring.naming import titleize
from ..types import TargetFunction, SetupParserFunction
from ._codeobject import Module


logger = logging.getLogger(__name__)


def emit(
    m: Module,
    fn: TargetFunction,
    *,
    cleanup_code: t.Callable[[str], str],
    inplace: bool = False,
):
    target_file = inspect.getsourcefile(fn)
    source = pathlib.Path(target_file).read_text()
    cleaned = cleanup_code(source)

    def _dump(out):
        print(cleaned, file=out)
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
        pathlib.Path(target_file).write_text(code)
    finally:
        if outpath and outpath.exists():
            outpath.unlink(missing_ok=True)
    sys.exit(1)


def run_as_single_command(
    setup_parser: SetupParserFunction[TargetFunction],
    *,
    fn: TargetFunction,
    argv: t.Optional[str],
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

        # # adding code, by self.setup_parser(). e.g.
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

    def cleanup_code(source: str) -> str:
        from prestring.python.parse import parse_string, PyTreeVisitor, type_repr
        from lib2to3.pytree import Node
        from ._ast import CollectSymbolVisitor

        ast = parse_string(source)
        visitor = CollectSymbolVisitor()
        visitor.visit(ast)
        symbols = visitor.symbols

        will_be_removed = set()
        for sym in symbols.values():
            if sym.fullname == "handofcats.as_command":
                will_be_removed.add(sym.id)

        class RemoveNodeVisitor(PyTreeVisitor):
            def visit_import_name(self, node: Node) -> t.Optional[bool]:
                if id(node) in will_be_removed:
                    node.remove()
                return True

            def visit_import_from(self, node: Node) -> t.Optional[bool]:
                if id(node) in will_be_removed:
                    node.remove()
                return True

            def visit_decorator(self, node: Node) -> t.Optional[bool]:
                # @ [ <dotted_name> | Leaf ]
                assert type_repr(node.children[0].value) == "@"
                for x in node.children:
                    if hasattr(x, "value") and x.value in symbols:
                        if symbols.get(x.value).fullname == "handofcats.as_command":
                            node.remove()
                            return True
                return True

        RemoveNodeVisitor().visit(ast)
        return str(ast)

    emit(m, fn, inplace=inplace, cleanup_code=cleanup_code)


def run_as_multi_command(
    setup_parser: SetupParserFunction[t.List[TargetFunction]],
    *,
    functions: t.List[TargetFunction],
    argv: t.Optional[str] = None,
    outname: str = "main",
    inplace: bool = False,
    typed: bool = False,
) -> t.Any:
    """ generate main() code

    something like

    ```
    def main(argv=None):
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
        subparsers.required = True

        fn = <fn 1>
        sub_parser = subparsers.add_parser(fn.__name__, help=fn.__doc__)
        # # adding code, by self.setup_parser(). e.g.
        # parser.add_argument('--name', required=False, default='world', help="(default: 'world')")
        # parser.add_argument('--debug', action="store_true")
        sub_parser.set_defaults(subcommand=fn)

        fn = <fn 2>
        sub_parser = subparsers.add_parser(fn.__name__, help=fn.__doc__)
        # # adding code, by self.setup_parser(). e.g.
        # sub_parser.add_argument('filename')
        sub_parser.set_defaults(subcommand=fn)

        ...

        args = parser.parse_args(argv)
        params = vars(args).copy()
        subcommand = params.pop('subcommand')
        return subcommand(**params)


    if __name__ == '__main__':
        main()
    ```
    """

    m = Module()
    m.toplevel = m.submodule()

    if outname in [fn.__name__ for fn in functions]:
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
        parser, _ = setup_parser(m, functions, customizations=[])

        # args = parser.parse_args(argv)
        args = m.let("args", parser.parse_args(m.symbol("argv")))

        # params = vars(args).copy()
        params = m.let("params", m.symbol("vars")(args).copy())

        # subcommand = params.pop("subcommand")
        m.let("subcommand", params.pop("subcommand"))

        # return subcommand(**params)
        m.return_(f"subcommand(**params)")

    # if __name__ == "__main__":
    with m.if_("__name__ == '__main__'"):
        # main()
        m.stmt(f"{outname}()")

    def cleanup_code(source: str) -> str:
        from prestring.python.parse import (
            parse_string,
            PyTreeVisitor,
            type_repr,
            node_name,
        )
        from lib2to3.pytree import Node
        from ._ast import CollectSymbolVisitor

        ast = parse_string(source)
        visitor = CollectSymbolVisitor()
        visitor.visit(ast)
        imported_symbols = visitor.symbols
        candidates = []

        will_be_removed = set()
        for sym in imported_symbols.values():
            if sym.fullname == "handofcats.as_subcommand":
                will_be_removed.add(sym.id)
                candidates.append(f"@{sym.name}.register")
                candidates.append(f"@{sym.name}")
                candidates.append(f"{sym.name}.run(")
            elif sym.fullname == "handofcats":
                will_be_removed.add(sym.id)
                candidates.append(f"@{sym.name}.as_subcommand.register")
                candidates.append(f"@{sym.name}.as_subcommand")
                candidates.append(f"{sym.name}.as_subcommand.run(")

        class RemoveNodeVisitor(PyTreeVisitor):
            def visit_import_name(self, node: Node) -> t.Optional[bool]:
                if id(node) in will_be_removed:
                    node.remove()
                return True

            def visit_import_from(self, node: Node) -> t.Optional[bool]:
                if id(node) in will_be_removed:
                    node.remove()
                return True

            def visit_decorator(self, node: Node) -> t.Optional[bool]:
                # remove @as_subcommand
                assert type_repr(node.children[0].value) == "@"
                stmt = str(node)
                for x in candidates:
                    if x in stmt:
                        node.remove()
                        return True
                return True

            def visit_simple_stmt(self, node: Node) -> t.Optional[bool]:
                # remove as_subcommand.run
                stmt = str(node)
                if "@" in stmt:
                    return False  # continue
                for x in candidates:
                    if x in stmt:
                        parent = node.parent
                        node.remove()
                        if not str(parent).strip():
                            assert node_name(parent.children[-1]) == "DEDENT"
                            parent.children[-1].prefix = "pass\n"
                        return True
                return False  # continue

        RemoveNodeVisitor().visit(ast)
        return str(ast)

    fake = functions[0]
    emit(m, fake, inplace=inplace, cleanup_code=cleanup_code)
