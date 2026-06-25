from fastapi import FastAPI

from app.api.routes.files import router as files_router
from app.api.routes.gold import router as gold_router
from app.api.routes.health import router as health_router
from app.api.routes.manual import router as manual_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema de Decisao Financeira Pessoal",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(files_router)
    app.include_router(manual_router)
    app.include_router(gold_router)
    return app


app = create_app()
