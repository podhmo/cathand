# handofcats

<https://travis-ci.org/podhmo/handofcats.svg>

A tiny magically Converter that making executable command script from
plain python function. If the function is type annotated, it is used.

  - If you want single-command, `as_command()` is helpful ✨
  - If you want sub-commands, `as_subcommand()` is helpful ✨
  - If you want something like [create-react-app's eject](https://github.com/facebook/create-react-app#philosophy), use `--expose` option](https://github.com/podhmo/handofcats#--expose) ◀️

## `as_command()`

greeting.py

``` python
from handofcats import as_command

@as_command
def greeting(message: str, is_surprised: bool = False, name: str = "foo") -> None:
    """greeting message"""
    suffix = "!" if is_surprised else ""
    print("{name}: {message}{suffix}".format(name=name, message=message, suffix=suffix))
```

🚀 Using as single-command

``` console
$ python greeting.py hello
foo: hello
$ python greeting.py --is-surprised hello
foo: hello!
$ python greeting.py --is-surprised --name=bar bye
bar: bye!
```

help message

``` console
$ python greeting.py -h
usage: greeting [-h] [--is-surprised] [--name NAME] [--expose] [--inplace]
                [--untyped]
                [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
                message

greeting message

positional arguments:
  message

optional arguments:
  -h, --help            show this help message and exit
  --is-surprised
  --name NAME           (default: 'foo')
  --expose              dump generated code. with --inplace, eject from
                        handofcats dependency
  --inplace             overwrite file
  --untyped             untyped expression is dumped (default: False)
  --logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
```

( :warning: TODO: detail description )

## `as_subcommand()` and `as_subcommand.run()`

If you want sub-commands, from following code.

cli.py

``` python
from handofcats import as_subcommand


@as_subcommand
def hello(*, name: str = "world"):
    print(f"hello {name}")


@as_subcommand
def byebye(name):
    print(f"byebye {name}")


# :warning: don't forget this
as_subcommand.run()
```

🚀 Using as sub-commands

``` cosole
$ python cli.py hello
hello world

$ python cli.py hello --name foo
hello foo

$ python cli.py byebye foo
byebye foo
```

help message

``` cosole
$ python cli.py -h
usage: cli.py [-h] [--expose] [--inplace] [--untyped]
              [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
              {hello,byebye} ...

optional arguments:
  -h, --help            show this help message and exit
  --expose              dump generated code. with --inplace, eject from handofcats dependency (default: False)
  --inplace             overwrite file
  --untyped             untyped expression is dumped (default: False)
  --logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}

subcommands:
  {hello,byebye}
    hello
    byebye


$ python cli.py hello -h
usage: cli.py hello [-h] [--name NAME]

optional arguments:
  -h, --help   show this help message and exit
  --name NAME  (default: 'world')
```

# `--expose`

Runing with `--expose` option, generationg the code that dropping
dependencies of handofcats module.

Something like [create-react-app'seject](https://github.com/facebook/create-react-app#philosophy) .

> No Lock-In: You can “eject” to a custom setup at any time. Run a single-command, and all the configuration and build dependencies will be moved directly into your project, so you can pick up right where you left off.

If you want to eject from [the code described above](https://github.com/podhmo/handofcats#as_command), `--expose` is helpful, maybe.

``` console
$ python greeting.py --expose
import typing as t

def greeting(message: str, is_surprised: bool = False, name: str = "foo") -> None:
    """greeting message"""
    suffix = "!" if is_surprised else ""
    print("{name}: {message}{suffix}".format(name=name, message=message, suffix=suffix))


def main(argv: t.Optional[t.List[str]] = None) -> t.Any:
    import argparse

    parser = argparse.ArgumentParser(prog=greeting.__name__, description=greeting.__doc__, formatter_class=type('_HelpFormatter', (argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter), {}))
    parser.print_usage = parser.print_help  # type: ignore
    parser.add_argument('message', help='-')
    parser.add_argument('--is-surprised', action='store_true', help='-')
    parser.add_argument('--name', required=False, default='foo', help='-')
    args = parser.parse_args(argv)
    params = vars(args).copy()
    return greeting(**params)


if __name__ == '__main__':
    main()
```

## `--expose` with `--inplace`

In addition, running with `inplace` option, when `--expose`, overwrite
target source code.

# `handofcats` command

sum.py

``` python
def sum(x: int, y: int) -> None:
    print(f"{x} + {y} = {x + y}")
```


It is also ok, calling the function that not decorated via handofcats
command.

``` console
$ handofcats sum.py:sum 10 20
10 + 20 = 30

$ handofcats sum.py:sum -h
handofcats sum.py:sum -h
usage: sum [-h] [--expose] [--inplace] [--untyped]
           [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
           x y

positional arguments:
  x
  y

optional arguments:
  -h, --help            show this help message and exit
  --expose              dump generated code. with --inplace, eject from handofcats dependency (default: False)
  --inplace             overwrite file
  --untyped             untyped expression is dumped (default: False)
  --logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
```

# `--expose` with handofcats command

Passed in the form `<filename>.py`, it will be interpreted as a
sub-commands. Of course, the `--expose` option also works.

And passed in the form `<filename>.py:<function name>`, it will be
interpreted as a single-command.

So, plain python function only needed.

<details>

cli.py

``` python
def hello(*, name: str = "world"):
    print(f"hello {name}")


# FIXME: default arguments (positional arguments)
def byebye(name: str):
    print(f"byebye {name}")


# ignored
def _ignore(name: str):
    print("ignored")
```

``` console
# treated as sub-commands
$ handofcats cli.py --expose
import typing as t

def hello(*, name: str = "world"):
    print(f"hello {name}")


# FIXME: default arguments (positional arguments)
def byebye(name: str):
    print(f"byebye {name}")


# ignored
def ignore(name: str):
    print(f"ignored {name}")


def _ignore(name: str):
    print("of cource, ignored")


def main(argv: t.Optional[t.List[str]] = None) -> t.Any:
    import argparse

    parser = argparse.ArgumentParser(formatter_class=type('_HelpFormatter', (argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter), {}))
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')
    subparsers.required = True

    fn = hello
    sub_parser = subparsers.add_parser(fn.__name__, help=fn.__doc__, formatter_class=parser.formatter_class)
    sub_parser.add_argument('--name', required=False, default='world', help='-')
    sub_parser.set_defaults(subcommand=fn)

    fn = byebye  # type: ignore
    sub_parser = subparsers.add_parser(fn.__name__, help=fn.__doc__, formatter_class=parser.formatter_class)
    sub_parser.add_argument('name', help='-')
    sub_parser.set_defaults(subcommand=fn)

    args = parser.parse_args(argv)
    params = vars(args).copy()
    subcommand = params.pop('subcommand')
    return subcommand(**params)


if __name__ == '__main__':
    main()


# treated as single-command
$ handofcats cli.py:hello --expose
...
```

</details>

# experimental

## sequences

``` python
from typing import List, Optional

def psum(xs: List[int], *, ys: Optional[List[int]] = None):
    # treated as
    # parser.add_argument('xs', nargs='*', type=int)
    # parser.add_argument('--ys', action='append', required=False, type=int)
    ..
```

## choices

``` python
from typing_extensions import Literal


DumpFormat = Literal["json", "csv"]   # this: (experimental)


def run(*, format: DumpFormat = "json"):
    # treated as
    # parser.add_argument("--format", defaul="json", choices=("json", "csv"), required=False)
    ...
```
