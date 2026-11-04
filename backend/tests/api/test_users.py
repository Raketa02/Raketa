from sqlalchemy import select

from app.infrastructure.events.event_store_model import EventStoreORM

NAMING = {"nickname": "alice"}


async def _signed_in(client, payload) -> dict[str, str]:
    """Sign this payload up and in; the bearer header for what follows."""

    assert (await client.post("/api/v1/users", json=payload)).status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_signup_success(client, valid_signup_payload):
    resp = await client.post("/api/v1/users", json=valid_signup_payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == valid_signup_payload["email"]
    assert body["authority"] == "USER"
    assert body["is_admin"] is False
    assert "password" not in body and "password_hash" not in body
    # Credentials only: a fresh account has no nickname (``docs/adr/0199`` §3),
    # and no account holds a name at all.
    assert body["nickname"] is None
    assert "name" not in body
    # The Tester mark went with the feature flags it fed (#581).
    assert "is_tester" not in body


async def test_signup_carrying_a_nickname_is_malformed(client, valid_signup_payload):
    """The nickname left the payload, and a body that still sends one is a body
    no shipped client sends — refused with the validation envelope rather than
    quietly ignored, so the client ticket cannot keep the field by accident."""

    resp = await client.post(
        "/api/v1/users", json={**valid_signup_payload, "nickname": "alice"}
    )

    assert resp.status_code == 422, resp.text


async def test_me_reads_no_nickname_until_the_naming(client, valid_signup_payload):
    """The entry gate's first destination reads *no nickname*
    (``docs/adr/0199`` §3), and ``/me`` serves no ``name`` at all."""

    headers = await _signed_in(client, valid_signup_payload)

    me = await client.get("/api/v1/users/me", headers=headers)

    assert me.status_code == 200, me.text
    assert me.json()["nickname"] is None
    assert "name" not in me.json()


async def test_the_naming_takes_a_nickname_and_me_reads_it(
    client, valid_signup_payload
):
    headers = await _signed_in(client, valid_signup_payload)

    named = await client.put(
        "/api/v1/users/me/name", json={"nickname": "ania.k"}, headers=headers
    )

    assert named.status_code == 200, named.text
    assert named.json() == {"nickname": "ania.k"}
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.json()["nickname"] == "ania.k"
    assert "name" not in me.json()


async def test_the_naming_requires_auth(client):
    resp = await client.put("/api/v1/users/me/name", json=NAMING)
    assert resp.status_code == 401


async def test_the_naming_is_repeatable(client, valid_signup_payload):
    """A later change is the same act, and keeping your own nickname is
    admitted (``docs/adr/0199`` §3)."""

    headers = await _signed_in(client, valid_signup_payload)
    assert (
        await client.put("/api/v1/users/me/name", json=NAMING, headers=headers)
    ).status_code == 200

    unchanged = await client.put(
        "/api/v1/users/me/name", json={"nickname": "alice"}, headers=headers
    )
    assert unchanged.status_code == 200, unchanged.text
    assert unchanged.json() == {"nickname": "alice"}

    renamed = await client.put(
        "/api/v1/users/me/name", json={"nickname": "ak.padel"}, headers=headers
    )
    assert renamed.status_code == 200, renamed.text
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.json()["nickname"] == "ak.padel"


async def test_a_nickname_given_up_is_free_to_take(client, valid_signup_payload):
    """Uniqueness reads the projection as it stands: once Alice moves on to a
    new handle, her old one is anybody's."""

    alice = await _signed_in(client, valid_signup_payload)
    bob = await _signed_in(client, {**valid_signup_payload, "email": "bob@example.com"})
    assert (
        await client.put("/api/v1/users/me/name", json=NAMING, headers=alice)
    ).status_code == 200
    assert (
        await client.put(
            "/api/v1/users/me/name", json={"nickname": "alice2"}, headers=alice
        )
    ).status_code == 200

    taken = await client.put("/api/v1/users/me/name", json=NAMING, headers=bob)

    assert taken.status_code == 200, taken.text


async def test_another_players_nickname_is_refused_with_the_conflict(
    client, valid_signup_payload
):
    alice = await _signed_in(client, valid_signup_payload)
    assert (
        await client.put("/api/v1/users/me/name", json=NAMING, headers=alice)
    ).status_code == 200
    bob = await _signed_in(client, {**valid_signup_payload, "email": "bob@example.com"})

    resp = await client.put(
        "/api/v1/users/me/name", json={"nickname": "alice"}, headers=bob
    )

    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "nickname_already_taken"
    assert resp.json()["details"] == {"field": "nickname"}
    me = await client.get("/api/v1/users/me", headers=bob)
    assert me.json()["nickname"] is None


async def test_the_naming_refuses_a_malformed_nickname_or_a_name(
    client, valid_signup_payload
):
    """``{nickname}`` and nothing else: a body still carrying a name is a body
    no client sends any more, refused rather than quietly dropped."""

    headers = await _signed_in(client, valid_signup_payload)

    for body in (
        {"nickname": "ali ce"},
        {"nickname": " ania.k "},
        {"nickname": "a"},
        {"nickname": "x" * 65},
        {"nickname": "ania@k"},
        {},
        {"name": "Alice"},
        {"name": "Alice Liddell", "nickname": "alice"},
        {"nickname": "alice", "extra": "field"},
    ):
        resp = await client.put("/api/v1/users/me/name", json=body, headers=headers)
        assert resp.status_code == 422, (body, resp.text)


async def test_the_naming_is_one_event_carrying_the_nickname_alone(
    client, valid_signup_payload, session_factory
):
    headers = await _signed_in(client, valid_signup_payload)
    assert (
        await client.put("/api/v1/users/me/name", json=NAMING, headers=headers)
    ).status_code == 200

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(EventStoreORM.payload, EventStoreORM.schema_version).where(
                    EventStoreORM.event_type == "users.user_named"
                )
            )
        ).all()

    assert len(rows) == 1
    payload, version = rows[0]
    assert version == 2
    assert payload["nickname"] == "alice"
    assert "name" not in payload


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


async def test_signup_password_mismatch(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password2": "different1!"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


async def test_signup_weak_password(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password1": "weak", "password2": "weak"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


async def test_signup_duplicate_email(client, valid_signup_payload):
    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201
    resp = await client.post("/api/v1/users", json=valid_signup_payload)
    assert resp.status_code == 409
    assert resp.json()["code"] == "email_already_registered"


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


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
    # No Tester mark: nothing reads one since the feature flags went (#581).
    assert "is_tester" not in resp.json()
