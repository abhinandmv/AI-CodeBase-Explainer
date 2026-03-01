from app.celery_app import celery
from app.config import settings
from app.storage import store
from app.utils import safe_mkdir
from app.services.git_service import shallow_clone
from app.services.analyzer import analyze_repo
from app.services.llm_service import generate_report_with_ollama

def _update(analysis_id: str, status: str, progress: int, error: str | None = None, result=None, cached: bool = False):
    store.update(analysis_id, status=status, progress=progress, error=error, result=result, cached=cached)


@celery.task(name="app.tasks.run_analysis")
def run_analysis(analysis_id: str, repository_url: str, repo_hash: str) -> None:
    try:
        _update(analysis_id, "processing", 5)

        safe_mkdir(settings.CLONE_DIR)
        safe_mkdir(settings.OUTPUT_DIR)

        repo_dir = os.path.join(settings.CLONE_DIR, repo_hash)

        _update(analysis_id, "processing", 15, error="Cloning repository...")
        shallow_clone(repository_url, repo_dir)

        _update(analysis_id, "processing", 55, error="Running static analysis...")
        analysis = analyze_repo(repo_dir)

        _update(analysis_id, "processing", 80, error="Generating LLM report...")
        report = generate_report_with_ollama(analysis)

        result = {
            "analysis_id": analysis_id,
            "repository_url": repository_url,
            "generated_at": int(time.time()),
            "analysis": analysis,
            "report": report,
        }

        store.cache_set(repo_hash, analysis_id)
        _update(analysis_id, "complete", 100, error=None, result=result)

    except Exception as e:
        _update(analysis_id, "failed", 100, error=str(e), result=None)