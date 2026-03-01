from typing import Dict, Any

def fallback_report(analysis: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "overview": {
            "one_liner": "Repository analyzed (fallback report).",
            "what_it_does": "Static analysis completed; AI report generation failed, showing extracted signals.",
            "primary_language": analysis.get("language", "Unknown"),
        },
        "architecture": {
            "style": "Unknown (fallback)",
            "entrypoints": analysis.get("entrypoints", []),
            "key_modules": [{"name": "N/A", "purpose": "AI generation unavailable"}],
            "data_flow": ["N/A"],
        },
        "dependencies": {
            "summary": "Extracted dependency signals only (fallback).",
            "high_impact": list(set(analysis.get("dependencies", {}).get("python", [])[:10] + analysis.get("dependencies", {}).get("node", [])[:10])),
        },
        "improvements": {
            "quick_wins": ["Add/Improve README", "Add basic tests", "Add CI workflow"],
            "risks": ["AI generation unavailable; validate manually."],
        },
        "important_files": analysis.get("important_files", []),
    }

def fallback_issue(issue_text: str, important_files: list[str]) -> Dict[str, Any]:
    return {
        "where_to_start": "Start by locating the entry point and the module that likely owns the feature mentioned in the issue.",
        "relevant_files": important_files[:8],
        "suggested_steps": [
            "Reproduce/understand current behavior",
            "Search codebase for keywords from the issue",
            "Identify the owning module and add a failing test if possible",
            "Implement fix/change and validate locally",
        ],
        "risk_points": ["Incomplete context due to AI fallback."],
        "test_recommendations": ["Add/Update unit test covering the issue scenario", "Run existing test suite if available"],
        "difficulty": "Medium",
    }