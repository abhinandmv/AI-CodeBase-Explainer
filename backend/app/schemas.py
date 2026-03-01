from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, Dict, List

Status = Literal["queued", "processing", "complete", "failed"]

class AnalyzeRequest(BaseModel):
    repository_url: str = Field(..., examples=["https://github.com/owner/repo"])

class AnalyzeResponse(BaseModel):
    analysis_id: str
    status: Status

class AnalysisStatusResponse(BaseModel):
    status: Status
    progress: int = Field(..., ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cached: bool = False

class IssueAssistRequest(BaseModel):
    analysis_id: str
    issue_text: str

class IssueAssistResponse(BaseModel):
    where_to_start: str
    relevant_files: List[str]
    suggested_steps: List[str]
    risk_points: List[str]
    test_recommendations: List[str]
    difficulty: Literal["Easy", "Medium", "Hard"]