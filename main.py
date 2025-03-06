from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.endpoints import router as endpoints_router
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# Include API endpoints
app.include_router(endpoints_router, prefix="/api", tags=["Endpoints"])

os.environ["PATH"] = os.path.expanduser("~") + "/edirect:" + os.environ["PATH"]