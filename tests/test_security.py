import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from common.security import (
    JWT_ALGORITHM,
    JWT_SECRET,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_et_verification():
    hashed = hash_password("motdepasse-test")
    assert hashed != "motdepasse-test"
    assert verify_password("motdepasse-test", hashed) is True
    assert verify_password("mauvais-mot-de-passe", hashed) is False


def test_creation_et_decodage_jwt():
    user = SimpleNamespace(id=42, role="manager")
    token = create_access_token(user)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "manager"
    assert "exp" in payload


def test_rejet_jwt_expire():
    expired = jwt.encode(
        {"sub": "42", "role": "manager", "exp": int(time.time()) - 60},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired)
    assert exc_info.value.status_code == 401


def test_rejet_jwt_signe_avec_un_autre_secret():
    forged = jwt.encode(
        {"sub": "42", "role": "manager", "exp": int(time.time()) + 3600},
        "un-autre-secret",
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(forged)
    assert exc_info.value.status_code == 401
