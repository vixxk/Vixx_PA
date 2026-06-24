from typing import Dict, Any
from app.graphs.state import WorkflowState

async def run_summary_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent")
    project = state.get("project")
    milestones = state.get("milestones") or []
    todos = state.get("todos") or []
    risks = state.get("risks") or []
    needs_clarification = state.get("needs_clarification", False)

    if intent != "create_project" or not project or needs_clarification:
        return {}

    title = project.get("title")
    description = project.get("description") or "No description."
    # Build Markdown Summary
    md = f"# Project Kickoff Plan: {title}\n\n"
    md += f"**Description:** {description}\n\n"

    md += "## 🎯 Milestones\n"
    for m in milestones:
        md += f"- **{m.get('title')}** ({m.get('start_date')} to {m.get('end_date')})\n"
        md += f"  *Description: {m.get('description')}*\n"
    md += "\n"

    md += "## 📋 Sprints & Tasks breakdown\n"
    for t in todos:
        md += f"- **{t.get('title')}** ({t.get('estimated_hours')} hours, Due: {t.get('due_date')})\n"
        md += f"  *Details: {t.get('description')}*\n"
    md += "\n"

    md += "## ⚠️ Risk Mitigation Matrix\n"
    for r in risks:
        md += f"- **{r.get('risk_name')}** [Severity: {r.get('severity').upper()}]\n"
        md += f"  *Impact:* {r.get('description')}\n"
        md += f"  *Mitigation:* {r.get('mitigation')}\n"

    return {
        "summary": md
    }
