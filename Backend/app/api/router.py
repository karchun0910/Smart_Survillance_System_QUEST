from fastapi import APIRouter

from app.api.routes.cameras import router as cameras_router
from app.api.routes.health import router as health_router
from app.api.routes.rules import router as rules_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(rules_router, tags=["rules"])
api_router.include_router(cameras_router, tags=["cameras"])
