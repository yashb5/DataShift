import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.middleware.correlation_id import CorrelationIdMiddleware, CorrelationIdFilter
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.routers import (
    connections_router,
    pipelines_router,
    alerts_router,
    observability_router,
)
from app.health import router as health_router
from app.metrics import router as metrics_router

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
)

for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DataShift application...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down DataShift application...")


app = FastAPI(
    title="DataShift",
    description="Simple tool to move data between databases",
    version="1.0.0",
    docs_url="/swagger-ui.html",
    redoc_url="/redoc",
    openapi_url="/v3/api-docs",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(connections_router)
app.include_router(pipelines_router)
app.include_router(alerts_router)
app.include_router(observability_router)
app.include_router(health_router, prefix="/actuator")
app.include_router(metrics_router, prefix="/actuator")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "Simple tool to move data between databases",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=settings.debug,
    )
