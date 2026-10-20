"""Password and credential helpers kept free of UI dependencies."""

import hmac
import re


BCRYPT_HASH = re.compile(r"^\$2[abxy]?\$\d{2}\$[./A-Za-z0-9]{53}$")


def secure_equals(left, right):
    """Compare two values in constant time, including non-ASCII text."""
    return hmac.compare_digest(str(left).encode("utf-8"), str(right).encode("utf-8"))


def make_hashes(password):
    """Hash a password with bcrypt."""
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_hashes(password, hashed_text):
    """Return True only when the stored hash is a valid bcrypt hash matching the password."""
    if not isinstance(hashed_text, str) or not BCRYPT_HASH.match(hashed_text):
        return False
    try:
        import bcrypt

        return bcrypt.checkpw(password.encode(), hashed_text.encode())
    except (ValueError, TypeError):
        return False
