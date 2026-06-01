from typing import Protocol, runtime_checkable


@runtime_checkable
class UnitOfWork(Protocol):
    """Transactional boundary consumed by application use cases."""

    async def commit(self) -> None: ...

    async def flush(self) -> None: ...

    async def rollback(self) -> None: ...
