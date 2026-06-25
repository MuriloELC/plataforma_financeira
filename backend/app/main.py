from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.files import router as files_router
from app.api.routes.gold import router as gold_router
from app.api.routes.health import router as health_router
from app.api.routes.manual import router as manual_router
from app.api.routes.purchase_decisions import router as purchase_decisions_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Sistema de Decisao Financeira Pessoal",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(files_router)
    app.include_router(manual_router)
    app.include_router(gold_router)
    app.include_router(purchase_decisions_router)
    return app


app = create_app()
