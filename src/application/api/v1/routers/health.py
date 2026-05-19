from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    # Deliberately does not hit the DB — ALB / ECS healthchecks should not
    # destabilise on transient DB blips. Use a dedicated /ready endpoint if
    # readiness coupling is needed.
    return {"status": "ok"}
