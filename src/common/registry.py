from collections.abc import Callable


class Registry:
    """クラスを登録するためのレジストリクラス"""

    def __init__(self, kind: str):
        self.kind = kind
        self._map = {}

    def register(self, name: str) -> Callable[[type], type]:
        """クラスを登録するためのデコレータ

        Args:
            name(str): クラス名

        Returns:
            Callable[[type], type]: クラスを登録するためのデコレータ

        Examples:
            @DataBaseRegistry.register("duckdb")
            @dataclass(frozen=True)
            class DuckDBConfig(DataBaseConfig):
                ...

        """

        def wrapper(cls):
            self._map[name] = cls
            return cls

        return wrapper

    def __call__(self, name: str, *args, **kwargs):
        if name not in self._map:
            raise ValueError(f"Unknown {self.kind}: {name!r}")
        return self._map[name](*args, **kwargs)

    def __getitem__(self, name: str) -> type:
        return self._map[name]


class NestedRegistry:
    """2軸レジストリ"""

    def __init__(self, kind: str):
        self.kind = kind
        self._map: dict[str, dict[str, type]] = {}  # {category: {implementation: cls}}

    def register(self, category: str, impl: str) -> Callable[[type], type]:
        """クラスを登録するためのデコレータ

        Args:
            category(str): カテゴリ
            impl(str): 実装

        Returns:
            Callable[[type], type]: クラスを登録するためのデコレータ

        Examples:
            @RepositoryAdapterRegistry.register("images", "duckdb")
            class DuckDBImagesRepository(ImagesRepository, DebuggableRepository, BaseDuckDBRepository):
                ...
        """

        def wrapper(cls):
            self._map.setdefault(category, {})[impl] = cls
            return cls

        return wrapper

    def get(self, category: str, impl: str) -> type:
        try:
            return self._map[category][impl]
        except KeyError:
            raise ValueError(f"Unknown {self.kind}: category={category}, impl={impl!r}") from None

    def __call__(self, category: str, impl: str) -> type:
        return self.get(category, impl)
