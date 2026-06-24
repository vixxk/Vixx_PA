import json
import re
from typing import Dict, Any
from app.graphs.state import WorkflowState
from app.utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

async def run_risk_agent(state: WorkflowState) -> Dict[str, Any]:
    intent = state.get("intent")
    project = state.get("project")
    needs_clarification = state.get("needs_clarification", False)

    if intent != "create_project" or not project or needs_clarification:
        return {}

    title = project.get("title")
    description = project.get("description") or "No description provided."
    deadline = project.get("deadline")
    priority = project.get("priority") or "medium"
    
    risks = []
    
    try:
        llm = get_llm()
        system_prompt = (
            "You are a Project Risk Analyst agent. Your job is to identify potential risks, timeline crunches, "
            "and engineering blockers for a proposed project based on its description, priority, and deadline.\n\n"
            f"Project: {title}\n"
            f"Description: {description}\n"
            f"Deadline: {deadline}\n"
            f"Priority: {priority}\n\n"
            "Generate 2-3 potential risks. For each risk, provide:\n"
            "- risk_name: title of the risk\n"
            "- description: detailed explanation of the threat\n"
            "- severity: 'low', 'medium', 'high', or 'critical'\n"
            "- mitigation: realistic strategy to resolve or prevent this risk\n\n"
            "Format the output strictly as a JSON object with a 'risks' key containing the list. "
            "Do not include any other text."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Identify risks for project '{title}'")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            risks = data.get("risks", [])
            
    except Exception as e:
        # Fallback risks if LLM fails
        risks = [
            {
                "risk_name": "Timeline Constraints",
                "description": "The current deadline may be too aggressive for the scope described.",
                "severity": "high",
                "mitigation": "Scope down the MVP to focus solely on essential features."
            },
            {
                "risk_name": "System Integration Blocks",
                "description": "Third-party APIs or auth settings can take longer than estimated to configure.",
                "severity": "medium",
                "mitigation": "Kick off integration research and credentials setup on day 1."
            }
        ]

    return {
        "risks": risks
    }
