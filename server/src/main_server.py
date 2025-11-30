from fastapi import FastAPI
from datetime import datetime
from common.models import HealthResponse

app = FastAPI(title="TMC Warehouse API", version="1.0.0")


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", time=datetime.utcnow())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
