import sentry_sdk
import sentry_sdk.integrations.fastapi
import sentry_sdk.integrations.sqlalchemy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import (
    auth,
    categories,
    health,
    orders,
    products,
    public,
    restaurants,
    websocket,
)
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import configure_logging, request_logging_middleware

# Configure structured JSON logging before anything else.
configure_logging()

# Initialize Sentry when a DSN is provided (production / staging).
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            sentry_sdk.integrations.fastapi.FastApiIntegration(),
            sentry_sdk.integrations.sqlalchemy.SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

app = FastAPI(
    title="Tablio API",
    description=(
        "Backend de Tablio — menú digital y pedidos para "
        "negocios gastronómicos en Latam."
    ),
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_logging_middleware)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(restaurants.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
app.include_router(public.router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket.router)
