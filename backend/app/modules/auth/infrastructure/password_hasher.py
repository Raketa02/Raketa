import hashlib

import bcrypt

_BCRYPT_LIMIT = 72
_SHA256_PREFIX = "sha256$"


class BcryptPasswordHasher:
    """`PasswordHasher` port implementation — bcrypt with random salt.

    `rounds` is the work factor new hashes are made at, and only that. `verify`
    never reads it: bcrypt stores the cost inside every hash, so a hash made at
    one setting keeps verifying after the setting changes.
    """

    def __init__(self, *, rounds: int) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > _BCRYPT_LIMIT:
            digest = hashlib.sha256(password_bytes).hexdigest().encode("ascii")
            hashed = bcrypt.hashpw(digest, self._salt()).decode("utf-8")
            return f"{_SHA256_PREFIX}{hashed}"
        return bcrypt.hashpw(password_bytes, self._salt()).decode("utf-8")

    def _salt(self) -> bytes:
        return bcrypt.gensalt(rounds=self._rounds)

    def verify(self, password: str, password_hash: str) -> bool:
        password_bytes = password.encode("utf-8")
        try:
            if password_hash.startswith(_SHA256_PREFIX):
                digest = hashlib.sha256(password_bytes).hexdigest().encode("ascii")
                bcrypt_hash = password_hash.removeprefix(_SHA256_PREFIX).encode("utf-8")
                return bcrypt.checkpw(digest, bcrypt_hash)

            if bcrypt.checkpw(password_bytes, password_hash.encode("utf-8")):
                return True

            if len(password_bytes) > _BCRYPT_LIMIT:
                legacy_bytes = password_bytes[:_BCRYPT_LIMIT]
                return bcrypt.checkpw(legacy_bytes, password_hash.encode("utf-8"))

            return False
        except (ValueError, TypeError):
            return False
