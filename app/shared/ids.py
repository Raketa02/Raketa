import uuid
from uuid import UUID


def new_uuid() -> UUID:
    return uuid.uuid4()


def new_hex_id() -> str:
    return uuid.uuid4().hex


def parse_uuid(value: str) -> UUID:
    return UUID(value)
