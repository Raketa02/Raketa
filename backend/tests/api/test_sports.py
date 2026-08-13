import pytest

# The registry the client must receive verbatim — see app/kernel/sports.py.
EXPECTED = {
    "PADEL": {"players": 4, "durations": [60, 90, 120]},
    "TENNIS": {"players": 2, "durations": [60, 90]},
    "SQUASH": {"players": 2, "durations": [45, 60, 90]},
    "BADMINTON": {"players": 4, "durations": [60, 90]},
}


@pytest.mark.asyncio
async def test_sports_endpoint_returns_the_full_registry(client):
    resp = await client.get("/api/v1/sports")
    assert resp.status_code == 200, resp.text

    sports = resp.json()["sports"]
    by_sport = {row["sport"]: row for row in sports}

    assert set(by_sport) == set(EXPECTED)
    for sport, spec in EXPECTED.items():
        assert by_sport[sport]["players"] == spec["players"]
        assert by_sport[sport]["durations"] == spec["durations"]


@pytest.mark.asyncio
async def test_sports_endpoint_lists_exactly_four_sports(client):
    resp = await client.get("/api/v1/sports")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["sports"]) == 4
