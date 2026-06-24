import httpx
from typing import Dict, Any, List

async def create_google_calendar_event(
    access_token: str,
    event_title: str,
    event_description: str,
    due_date_str: str
) -> Dict[str, Any]:
    """
    Creates a single event in the user's primary Google Calendar.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Standardize date format to YYYY-MM-DD
    # Set date as a whole-day event or assign default times
    date_val = due_date_str.split("T")[0]
    
    event_body = {
        "summary": event_title,
        "description": event_description,
        "start": {
            "date": date_val
        },
        "end": {
            "date": date_val
        }
    }
    
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=event_body, headers=headers)
        if res.status_code == 200:
            return {"success": True, "event_id": res.json().get("id")}
        return {"success": False, "error": f"Failed to create calendar event: {res.text}"}

async def sync_milestones_to_calendar(
    access_token: str,
    milestones: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Syncs multiple milestones to Google Calendar.
    """
    results = []
    for m in milestones:
        due_date = m.get("end_date") or m.get("start_date")
        if not due_date:
            continue
            
        res = await create_google_calendar_event(
            access_token=access_token,
            event_title=f"Milestone: {m['title']}",
            event_description=m.get("description", ""),
            due_date_str=due_date
        )
        results.append({"milestone": m["title"], "result": res})
    return results
