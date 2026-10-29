import pytest

from security.authentication import hash_password, verify_password


def test_password_hash_verifies_correct_password():
    password = "Correct-Horse-Battery-7!"
    stored = hash_password(password)
    assert stored != password
    assert verify_password(password, stored)


def test_password_hash_rejects_wrong_password():
    stored = hash_password("Correct-Horse-Battery-7!")
    assert not verify_password("wrong-password-123", stored)


def test_password_hash_requires_twelve_characters():
    with pytest.raises(ValueError):
        hash_password("short")
