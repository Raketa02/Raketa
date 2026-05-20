from dataclasses import dataclass, field
from typing import Generic, List, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageRequest:
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 500:
            raise ValueError("limit must be between 1 and 500")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: List[T] = field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total
