from fastapi import FastAPI

from app.api.web_requests import router as web_requests_router


app = FastAPI(title="CargoPT API")
app.include_router(web_requests_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
