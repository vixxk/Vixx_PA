import httpx
from typing import Dict, Any, List

async def create_github_issue(
    token: str,
    repo: str, # Format: "owner/repo"
    title: str,
    body: str,
    labels: List[str] = None
) -> Dict[str, Any]:
    """
    Creates an issue in a GitHub repository.
    """
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    issue_data = {
        "title": title,
        "body": body,
        "labels": labels or []
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=issue_data, headers=headers)
        if res.status_code == 201:
            return {"success": True, "issue_url": res.json().get("html_url")}
        return {"success": False, "error": f"Failed to create GitHub issue: {res.text}"}

async def sync_todos_to_github(
    token: str,
    repo: str,
    todos: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Syncs multiple todos/tasks to GitHub issues.
    """
    results = []
    for t in todos:
        labels = [t.get("priority", "medium")]
        body = t.get("description", "")
        if t.get("estimated_hours"):
            body += f"\n\n**Estimated Time:** {t['estimated_hours']} hours"
            
        res = await create_github_issue(
            token=token,
            repo=repo,
            title=t["title"],
            body=body,
            labels=labels
        )
        results.append({"todo": t["title"], "result": res})
    return results
