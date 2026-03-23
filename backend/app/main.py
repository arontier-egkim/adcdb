from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.routers import adcs, antibodies, antigens, linkers, payloads, search, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="ADCDB", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(adcs.router)
app.include_router(antibodies.router)
app.include_router(antigens.router)
app.include_router(linkers.router)
app.include_router(payloads.router)
app.include_router(search.router)
app.include_router(stats.router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
