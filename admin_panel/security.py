from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    return "scrypt$16384$8$1$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(derived).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("scrypt$"):
        try:
            _, n, r, p, salt_b64, digest_b64 = stored_hash.split("$", maxsplit=5)
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=int(n),
                r=int(r),
                p=int(p),
            )
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False

    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def make_session_token(
    *,
    username: str,
    secret_key: str,
    max_age: int,
) -> str:
    payload = {
        "u": username,
        "exp": int(time.time()) + max_age,
        "nonce": secrets.token_hex(8),
    }
    encoded_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        secret_key.encode("utf-8"),
        encoded_payload,
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload.decode('ascii')}.{signature}"


def parse_session_token(token: str, secret_key: str) -> str | None:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        payload = json.loads(
            base64.urlsafe_b64decode(encoded_payload.encode("ascii")).decode("utf-8")
        )
        if int(payload["exp"]) < int(time.time()):
            return None
        return str(payload["u"])
    except Exception:
        return None
