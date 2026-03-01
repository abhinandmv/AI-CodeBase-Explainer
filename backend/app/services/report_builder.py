from typing import Dict, Any, List

SYSTEM_REPORT = """You are a senior software architect.
Return ONLY valid JSON.
No markdown, no extra text.
Follow the schema exactly.
"""

def build_repo_report_prompt(analysis: Dict[str, Any]) -> str:
    # Keep it compact; we already enforce top important files.
    return f"""
Analyze this repository statically (do NOT execute code). Provide a developer-friendly report.

Return JSON schema:
{{
  "overview": {{
    "one_liner": string,
    "what_it_does": string,
    "primary_language": string
  }},
  "architecture": {{
    "style": string,
    "entrypoints": [string],
    "key_modules": [{{"name": string, "purpose": string}}],
    "data_flow": [string]
  }},
  "dependencies": {{
    "summary": string,
    "high_impact": [string]
  }},
  "improvements": {{
    "quick_wins": [string],
    "risks": [string]
  }},
  "important_files": [string]
}}

Repo signals:
Primary language: {analysis.get("language")}
Entrypoints: {analysis.get("entrypoints")}
Dependencies: {analysis.get("dependencies")}
Important files (paths): {analysis.get("important_files")}

File snippets:
{analysis.get("important_file_snippets")}
""".strip()

SYSTEM_ISSUE = """You are a senior maintainer helping a new contributor start working on a GitHub issue.
Return ONLY valid JSON.
No markdown, no extra text.
"""

def build_issue_prompt(report: Dict[str, Any], issue_text: str) -> str:
    important_files = report.get("important_files", [])
    arch = report.get("architecture", {})
    return f"""
Given this repo summary and an issue, suggest how to start.

Return JSON schema:
{{
  "where_to_start": string,
  "relevant_files": [string],
  "suggested_steps": [string],
  "risk_points": [string],
  "test_recommendations": [string],
  "difficulty": "Easy" | "Medium" | "Hard"
}}

Repo architecture:
{arch}

Important files:
{important_files}

Issue:
{issue_text}
""".strip()