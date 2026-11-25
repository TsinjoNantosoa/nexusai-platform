from app.core.security import hash_password, hash_token, new_token, tokens_equal, verify_password


def test_argon2_passwords_are_one_way_and_verifiable() -> None:
    password_hash = hash_password("fictional-password-123")
    assert password_hash.startswith("$argon2id$")
    assert password_hash != "fictional-password-123"
    assert verify_password("fictional-password-123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_session_tokens_are_random_and_hashed() -> None:
    token = new_token()
    assert len(token) >= 40
    assert hash_token(token) != token
    assert tokens_equal(hash_token(token), hash_token(token))
    assert not tokens_equal(hash_token(token), hash_token(new_token()))
