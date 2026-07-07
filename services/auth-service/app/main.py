from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import test_db_connection
from app.api.health import router as health_router
from app.api.v1.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    if await test_db_connection():
        print("✅ Database ready")
    else:
        print("❌ Database connection failed")
        # Optionally raise exception to prevent startup
        raise RuntimeError("Cannot connect to database")
    
    yield  # App runs here
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {
        "message": "Auth Service Running"
    }

app.include_router(health_router)
app.include_router(auth_router)