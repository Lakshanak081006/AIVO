from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.demo import router as demo_router
from app.api.routes.health import router as health_router
from app.api.routes.simulated import router as simulated_router
from app.api.routes.travel import router as travel_router
from app.api.routes.users import router as users_router
api_router=APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(travel_router)
api_router.include_router(simulated_router)
api_router.include_router(demo_router)
