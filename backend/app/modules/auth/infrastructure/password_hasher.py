import hashlib

import bcrypt

_BCRYPT_LIMIT = 72
_SHA256_PREFIX = "sha256$"


class BcryptPasswordHasher:
    """`PasswordHasher` port implementation — bcrypt with random salt."""

    def hash(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > _BCRYPT_LIMIT:
            digest = hashlib.sha256(password_bytes).hexdigest().encode("ascii")
            hashed = bcrypt.hashpw(digest, bcrypt.gensalt()).decode("utf-8")
            return f"{_SHA256_PREFIX}{hashed}"
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

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
