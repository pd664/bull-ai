from fastapi import FastAPI
from app.api.upload import router as upload_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AlphaLens",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    upload_router
)

@app.get("/")
def health():
    return {
        "status": "healthy"
    }