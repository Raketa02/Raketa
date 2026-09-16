"""The envelope as a client actually receives it, over HTTP.

The unit test next door asserts the classes carry distinct codes; this one
asserts the wire does — including for the two failures no domain error authors,
a rejected body and an unrouted path, which a client must be able to map by code
like any other.
"""

import pytest

from app.core.tracing import TRACE_ID_HEADER


def _envelope(resp):
    body = resp.json()
    assert set(body) <= {"code", "message", "trace_id", "details"}
    assert body["code"] and body["message"] and body["trace_id"]
    return body


@pytest.mark.asyncio
async def test_a_domain_error_carries_its_own_code_not_its_base_class(
    client, valid_signup_payload
):
    await client.post("/api/v1/users", json=valid_signup_payload)

    resp = await client.post("/api/v1/users", json=valid_signup_payload)

    assert resp.status_code == 409
    body = _envelope(resp)
    assert body["code"] == "email_already_registered"
    # The field the client used to branch on is gone, deliberately: a rename is
    # free today and would later mean coordinating with phones in the wild.
    assert "error" not in resp.json()


@pytest.mark.asyncio
async def test_details_survive_onto_the_envelope(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)

    resp = await client.post("/api/v1/users", json=valid_signup_payload)

    assert resp.json()["details"] == {"field": "email"}


@pytest.mark.asyncio
async def test_every_error_carries_a_trace_id_matching_the_response_header(client):
    resp = await client.get("/api/v1/users/me")

    assert resp.status_code == 401
    body = _envelope(resp)
    assert body["trace_id"] == resp.headers[TRACE_ID_HEADER]


@pytest.mark.asyncio
async def test_a_successful_response_carries_a_trace_id_header_too(client):
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.headers[TRACE_ID_HEADER]


@pytest.mark.asyncio
async def test_two_requests_get_two_trace_ids(client):
    first = await client.get("/api/v1/users/me")
    second = await client.get("/api/v1/users/me")

    assert first.json()["trace_id"] != second.json()["trace_id"]


@pytest.mark.asyncio
async def test_a_supplied_trace_id_is_honoured(client):
    resp = await client.get(
        "/api/v1/users/me", headers={TRACE_ID_HEADER: "client-side-0001"}
    )

    assert resp.json()["trace_id"] == "client-side-0001"
    assert resp.headers[TRACE_ID_HEADER] == "client-side-0001"


@pytest.mark.asyncio
async def test_an_unsafe_supplied_trace_id_is_replaced(client):
    # The value reaches a log line, so a header is not trusted verbatim.
    resp = await client.get(
        "/api/v1/users/me", headers={TRACE_ID_HEADER: "not a trace id\nlevel=INFO"}
    )

    assert resp.json()["trace_id"] != "not a trace id\nlevel=INFO"
    assert resp.json()["trace_id"]


@pytest.mark.asyncio
async def test_missing_and_invalid_access_tokens_are_distinguishable(client):
    missing = await client.get("/api/v1/users/me")
    invalid = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"}
    )

    assert missing.status_code == invalid.status_code == 401
    assert missing.json()["code"] == "access_token_missing"
    assert invalid.json()["code"] == "access_token_invalid"


@pytest.mark.asyncio
async def test_a_401_still_challenges(client):
    resp = await client.get("/api/v1/users/me")

    assert resp.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_bad_credentials_have_their_own_code(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": valid_signup_payload["email"], "password": "wrong-password!"},
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_a_rejected_refresh_token_has_its_own_code(client):
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "nonsense"}
    )

    assert resp.status_code == 401
    # Not `unauthorized`, and not the same code a *valid but revoked* token
    # returns: a rotation that must sign the player out once is a different
    # recovery from one that must not.
    assert resp.json()["code"] == "invalid_refresh_token"


@pytest.mark.asyncio
async def test_a_rejected_body_is_the_same_envelope(client):
    resp = await client.post("/api/v1/users", json={"email": "not-an-email"})

    assert resp.status_code == 422
    body = _envelope(resp)
    assert body["code"] == "validation_error"
    assert "detail" not in resp.json()


@pytest.mark.asyncio
async def test_a_rejected_body_never_echoes_what_was_sent(client):
    # Pydantic's own error dicts carry the rejected input, and a rejected signup
    # body contains a password.
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "not-an-email",
            "password1": "hunter22!",
            "password2": "hunter22!",
            "adult_attested": True,
        },
    )

    assert resp.status_code == 422
    assert "hunter22!" not in resp.text


@pytest.mark.asyncio
async def test_an_unrouted_path_is_the_same_envelope(client):
    resp = await client.get("/api/v1/nothing-here")

    assert resp.status_code == 404
    assert _envelope(resp)["code"] == "not_found"


@pytest.mark.asyncio
async def test_status_semantics_are_unchanged(client, valid_signup_payload):
    # Only the body and its codes changed. A 409 is still a 409.
    await client.post("/api/v1/users", json=valid_signup_payload)

    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 409
    assert (await client.get("/api/v1/users/me")).status_code == 401
    assert (await client.post("/api/v1/users", json={})).status_code == 422
