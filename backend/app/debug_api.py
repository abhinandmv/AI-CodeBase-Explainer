from fastapi import APIRouter
from .services.llm_service import generate_report_with_ollama

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/llm")
def llm_debug():
    sample_analysis = {
        "language": "Python",
        "entrypoints": [],
        "dependencies": {"python": ["fastapi", "celery", "redis"], "node": [], "java": [], "other": []},
        "important_files": ["README.md"],
    }
    return generate_report_with_ollama(sample_analysis)