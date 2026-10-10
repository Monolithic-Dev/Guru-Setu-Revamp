"""GuruSetu API entry point (scaffold; replaced by the full app factory in T0.P2.1)."""
from fastapi import FastAPI

app = FastAPI(title="GuruSetu API")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}
