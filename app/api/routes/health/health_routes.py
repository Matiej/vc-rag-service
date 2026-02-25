from fastapi import APIRouter, Depends

from app.api.routes.health.app_info_response import AppInfoResponse
from app.service.app_info_service import AppInfoService

router = APIRouter()


def get_api_info_service():
    return AppInfoService()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/info", response_model=AppInfoResponse)
async def info(service: AppInfoService = Depends(get_api_info_service)):
    app_info = service.get_app_info()
    return AppInfoResponse(
        name=app_info.name,
        version=app_info.version,
        description=app_info.description,
        requires_python_version=app_info.requires_python_version
    )
