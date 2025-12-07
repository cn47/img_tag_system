from typing import Protocol


class SupportedRepository(Protocol):
    """サポートされるリポジトリ"""

    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class UnitOfWork:
    """Unit of Work実装"""

    def __init__(self, repositories: dict[str, SupportedRepository]) -> None:
        self.repositories = repositories

    def _validate_repositories(self, repos: dict[str, SupportedRepository]) -> None:
        if not isinstance(repos, dict):
            raise ValueError("repositories must be a dict. (key: repository name, value: Repository instance)")

        if not all(hasattr(repo, "commit") and hasattr(repo, "rollback") for repo in repos.values()):
            raise ValueError("repository values must have commit and rollback methods")

        if not all(isinstance(name, str) for name in repos):
            raise ValueError("repository keys must be strings (repository names)")

    @property
    def repositories(self) -> dict[str, SupportedRepository]:
        return self._repositories

    @repositories.setter
    def repositories(self, value: dict[str, SupportedRepository]) -> None:
        self._validate_repositories(value)
        self._repositories = value

    def __getitem__(self, name: str) -> SupportedRepository:
        if name in self._repositories:
            return self._repositories[name]
        raise AttributeError(f"Repository {name} not found")

    def subset(self, keys: list[str]) -> "UnitOfWork":
        return UnitOfWork(repositories={name: self.repositories[name] for name in keys})

    def _commit(self) -> None:
        for repository in self._repositories.values():
            repository.commit()

    def _rollback(self) -> None:
        for repository in self._repositories.values():
            repository.rollback()

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self._commit()
        else:
            self._rollback()
