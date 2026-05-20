import pytest


@pytest.mark.asyncio
async def test_me_returns_distinct_user_per_token(client):
    alice = {"email": "alice@example.com", "password1": "hunter22!",
             "password2": "hunter22!", "nickname": "alice"}
    bob = {"email": "bob@example.com", "password1": "hunter22!",
           "password2": "hunter22!", "nickname": "bob"}

    a_signup = await client.post("/api/v1/users", json=alice)
    b_signup = await client.post("/api/v1/users", json=bob)
    assert a_signup.status_code == 201 and b_signup.status_code == 201
    assert a_signup.json()["id"] != b_signup.json()["id"]

    a_login = await client.post(
        "/api/v1/auth/login",
        json={"email": alice["email"], "password": alice["password1"]},
    )
    b_login = await client.post(
        "/api/v1/auth/login",
        json={"email": bob["email"], "password": bob["password1"]},
    )
    a_tok = a_login.json()["access_token"]
    b_tok = b_login.json()["access_token"]
    assert a_tok != b_tok

    a_me = await client.get("/api/v1/users/me",
                            headers={"Authorization": f"Bearer {a_tok}"})
    b_me = await client.get("/api/v1/users/me",
                            headers={"Authorization": f"Bearer {b_tok}"})
    assert a_me.json()["email"] == "alice@example.com"
    assert b_me.json()["email"] == "bob@example.com"
    assert a_me.json()["id"] != b_me.json()["id"]
