from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .api import router as api_router
from .sse import progress_stream

app = FastAPI(title="Repo Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/api/analysis/{analysis_id}/stream")
async def stream(request: Request, analysis_id: str):
    return EventSourceResponse(progress_stream(request, analysis_id))