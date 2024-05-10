import pytest
from storeapi import security


def test_password_hashes():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.parametrize(
    "token_type",
    [
        "access",
        "confirmation",
    ],
)
def test_get_subject_for_token_type_valid(token_type: str):
    email = "test@example.com"
    token = security.create_access_token(email, token_type)
    assert email == security.get_subject_for_token_type(token, token_type)


@pytest.mark.parametrize(
    "token_type",
    [
        "access",
        "confirmation",
    ],
)
def test_get_subject_for_token_type_wrong_type(token_type):
    email = "test@example.com"
    token = security.create_access_token(email, token_type)
    map_reverse = {"access": "confirmation", "confirmation": "access"}
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, map_reverse[token_type])
    assert "Token has incorrect type, expected" in exc_info.value.detail


def test_get_subject_for_token_type_expired(mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has expired" == exc_info.value.detail
