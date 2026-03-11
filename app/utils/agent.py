import os
from typing import Any, Dict

import httpx


async def execute_agent(
    message: str,
    user_id: str,
    user_name: str,
    session_id: str,
) -> Dict[str, Any]:
    """Execute command through the agent"""
    agent_service_url = os.environ.get("AGENT_SERVICE_URL", "http://localhost:8001")
    async with httpx.AsyncClient(timeout=500.0) as client:
        response = await client.post(
            f"{agent_service_url}/agent/query",
            json={
                "message": message,
                "user_id": user_id,
                "user_name": user_name,
                "session_id": session_id,
            },
        )
        response.raise_for_status()
        return response.json().get("response", {})
