from fastapi import APIRouter, Request

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers(request: Request):
    return request.app.state.container.provider_capabilities()
