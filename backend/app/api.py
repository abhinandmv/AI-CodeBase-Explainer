import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .storage import store
from .utils import sha1
from .tasks import run_analysis
from .config import settings
from .utils import sha1, validate_github_repo_url
router = APIRouter(prefix="/api", tags=["api"])


class AnalyzeReq(BaseModel):
    repository_url: str


@router.post("/analyze")
def analyze(req: AnalyzeReq):
    repo_url = req.repository_url.strip()
    if not validate_github_repo_url(repo_url):
        raise HTTPException(status_code=400, detail="repository_url must be a valid GitHub repo URL")

    repo_hash = sha1(repo_url)

    cached_id = store.cache_get(repo_hash)
    if cached_id:
        state = store.get_analysis_state(cached_id)
        if state:
            # Return cached state directly
            state["cached"] = True
            return state

    # new analysis
    analysis_id = sha1(f"{repo_url}:{time.time()}")  # simple unique id
    store.set_analysis_state(
        analysis_id,
        {"status": "queued", "progress": 0, "result": None, "error": None, "cached": False},
        ttl=settings.ANALYSIS_TTL_SECONDS,
    )

    run_analysis.delay(analysis_id, repo_url, repo_hash)
    return store.get_analysis_state(analysis_id)


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    state = store.get_analysis_state(analysis_id)
    if not state:
        raise HTTPException(status_code=404, detail="analysis_id not found")
    return state