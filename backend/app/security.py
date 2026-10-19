"""Passwords and login tokens, using only Python's standard library.

- Passwords are hashed with scrypt (slow on purpose, with a random salt), so the
  database never holds a password, and a leaked database can't easily be cracked.
- A login is a random token kept by the browser in an httpOnly cookie. The
  database stores only its SHA-256, so a leaked database can't be used to log in.
"""

import hashlib
import hmac
import secrets

# scrypt cost: 2**14 rounds, ~16 MB memory per hash (recommended interactive-login settings)
_N, _R, _P, _KEY_LEN = 2**14, 8, 1, 32


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=_KEY_LEN, maxmem=64 * 1024 * 1024)


def hash_password(password: str) -> str:
    """'scrypt$n$r$p$salt$hash' (hex), safe to store."""
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, _N, _R, _P)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        # Still do the work, so a missing account takes as long as a wrong password
        _scrypt(password, b"0" * 16, _N, _R, _P)
        return False
    try:
        _, n, r, p, salt, digest = stored.split("$")
        expected = _scrypt(password, bytes.fromhex(salt), int(n), int(r), int(p))
    except ValueError:
        return False
    return hmac.compare_digest(expected.hex(), digest)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """What the database stores for a login token."""
    return hashlib.sha256(token.encode()).hexdigest()
