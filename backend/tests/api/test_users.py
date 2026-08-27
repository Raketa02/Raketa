import pytest
from sqlalchemy import select

from app.infrastructure.events.event_store_model import EventStoreORM


@pytest.mark.asyncio
async def test_signup_success(client, valid_signup_payload):
    resp = await client.post("/api/v1/users", json=valid_signup_payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == valid_signup_payload["email"]
    assert body["nickname"] == valid_signup_payload["nickname"]
    assert body["authority"] == "USER"
    assert body["is_admin"] is False
    assert "password" not in body and "password_hash" not in body


@pytest.mark.asyncio
async def test_signup_refuses_an_unanswered_age_question(client, valid_signup_payload):
    """The refusal is typed, and it names the control the client has to point at.

    A 400 with its own code, not the generic validation envelope: the body is
    well-formed and the player simply did not answer, which is a sentence the
    app has to write and therefore a code it has to be able to branch on.
    """

    payload = {**valid_signup_payload, "adult_attested": False}
    resp = await client.post("/api/v1/users", json=payload)

    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert body["code"] == "adult_attestation_required"
    assert body["details"] == {"field": "adult_attested"}


@pytest.mark.asyncio
async def test_signup_refuses_a_body_that_never_asked(client, valid_signup_payload):
    """A body that never asked is malformed, and that is the deliberate half.

    It could have been given a schema default of ``False`` and reached the typed
    400 like an unticked box does, which would put both *no answer* bodies into
    one renderable shape. **Required wins anyway**, because required is what
    makes the generated client type non-optional: a field defaulted here is
    ``adult_attested?: boolean`` on the client, and *forgot to ask* stops being a
    compile error over there. Refusing a malformed body with the validation
    envelope is the correct treatment of a body no shipped client sends.
    """

    payload = {k: v for k, v in valid_signup_payload.items() if k != "adult_attested"}
    resp = await client.post("/api/v1/users", json=payload)

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_refuses_before_it_reads_the_email(client, valid_signup_payload):
    """An unanswered question is refused without touching the account table.

    Otherwise a caller who attested to nothing learns which emails are taken —
    the refusal that costs nothing is the one that should come first.
    """

    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201

    resp = await client.post(
        "/api/v1/users", json={**valid_signup_payload, "adult_attested": False}
    )

    assert resp.status_code == 400
    assert resp.json()["code"] == "adult_attestation_required"


@pytest.mark.asyncio
async def test_signup_records_the_attestation_on_the_stream(
    client, valid_signup_payload, session_factory
):
    """The record is the event, and it is one boolean.

    Asserted on the stored payload rather than on a response field, because the
    attestation is deliberately not projected and not served: nothing downstream
    asks *how old*, only *may they be here*, and that was answered once.
    """

    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201

    async with session_factory() as session:
        payloads = (
            (
                await session.execute(
                    select(EventStoreORM.payload).where(
                        EventStoreORM.event_type == "users.user_registered"
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["adult_attested"] is True
    # Never a date of birth, and nothing one could be reconstructed from.
    assert not any("birth" in key or key == "age" for key in payload)


@pytest.mark.asyncio
async def test_signup_password_mismatch(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password2": "different1!"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_weak_password(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password1": "weak", "password2": "weak"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_duplicate_email(client, valid_signup_payload):
    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201
    dup = {**valid_signup_payload, "nickname": "alice2"}
    resp = await client.post("/api/v1/users", json=dup)
    assert resp.status_code == 409
    assert resp.json()["code"] == "email_already_registered"


@pytest.mark.asyncio
async def test_signup_duplicate_nickname(client, valid_signup_payload):
    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201
    dup = {**valid_signup_payload, "email": "alice2@example.com"}
    resp = await client.post("/api/v1/users", json=dup)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_access_token(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": valid_signup_payload["email"],
            "password": valid_signup_payload["password1"],
        },
    )
    access = login.json()["access_token"]
    resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {access}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == valid_signup_payload["email"]
