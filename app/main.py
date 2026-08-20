import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.macro import router as macro_router
from config import settings

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def _make_app(title: str) -> FastAPI:
    app = FastAPI(title=title, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(macro_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok", "env": settings.env}

    return app


app = _make_app("Macro Report API")
app_internal = _make_app("Macro Report API (Internal)")


async def _serve_both() -> None:
    cfg_ext = uvicorn.Config(
        "main:app", host="0.0.0.0", port=settings.port,
        log_level=settings.log_level.lower(),
    )
    cfg_int = uvicorn.Config(
        "main:app_internal", host="0.0.0.0", port=settings.internal_port,
        log_level=settings.log_level.lower(),
    )
    await asyncio.gather(
        uvicorn.Server(cfg_ext).serve(),
        uvicorn.Server(cfg_int).serve(),
    )


if __name__ == "__main__":
    asyncio.run(_serve_both())
