import typing as t
import inspect
from .util import reify
from collections import namedtuple


def option_name(name):
    return name.strip("_").replace("_", "-")


Option = namedtuple("Option", "name, option_name, required, type, default")


class Accessor:
    def __init__(self, fn):
        self.fn = fn

    @reify
    def resolver(self) -> "Resolver":
        return Resolver(self.fn)

    @reify
    def arguments(self) -> t.Sequence[Option]:
        r = []
        for name in self.resolver.argspec.args:
            if self.resolver.resolve_default(name) is None:
                r.append(self.create_positional(name))
        return r

    @reify
    def flags(self) -> t.Sequence[Option]:
        r = []
        for name in self.resolver.argspec.args:
            if self.resolver.resolve_default(name) is not None:
                r.append(self.create_flag(name, required=False))
        for name in self.resolver.argspec.kwonlyargs:
            required = self.resolver.resolve_default(name) is None
            r.append(self.create_flag(name, required=required))
        return r

    def create_flag(self, name, *, required: bool = False) -> Option:
        return Option(
            name=name,
            option_name=f"{'-' if len(name) <= 1 else '--'}{option_name(name)}",
            required=required,
            type=self.resolver.resolve_type(name),
            default=self.resolver.resolve_default(name),
        )

    def create_positional(self, name) -> Option:
        return Option(
            name=name,
            option_name=option_name(name),
            required=True,
            type=self.resolver.resolve_type(name),
            default=self.resolver.resolve_default(name),
        )


class Resolver:
    def __init__(self, fn):
        self.fn = fn
        self.argspec = inspect.getfullargspec(fn)

    @reify
    def _defaults(self) -> t.Dict[str, t.Any]:
        d = {}
        for i, v in enumerate(reversed(self.argspec.defaults or [])):
            k = self.argspec.args[-(i + 1)]  # 0 -> -1
            d[k] = v
        return d

    @reify
    def _kwonlydefaults(self) -> t.Dict[str, t.Any]:
        return self.argspec.kwonlydefaults or {}

    def resolve_default(self, name: str) -> t.Optional[t.Any]:
        return self._kwonlydefaults.get(name) or self._defaults.get(name)

    def resolve_type(self, name: str) -> t.Optional[t.Type]:
        if self.argspec.annotations is None:
            return None
        return self.argspec.annotations.get(name)