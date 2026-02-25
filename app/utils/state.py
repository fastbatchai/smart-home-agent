import os
import httpx
import streamlit as st
import asyncio
from typing import Any

from .auth import generate_thread_id

REFRESH_INTERVAL = 600  # seconds

async def fetch_home_state(user_name: str) -> dict[str, Any]:
    """Fetch home state from device service with caching"""
    device_service_url = os.environ.get("DEVICE_SERVICE_URL", "http://localhost:8000")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{device_service_url}/users/{user_name}/devices")
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        st.warning("Device service is taking longer than usual to respond")
        return st.session_state.get("home_state", {})
    except httpx.HTTPError as e:
        st.error(f"Failed to fetch home state: {str(e)}")
        return st.session_state.get("home_state", {})


async def initialize_session_state(config):
    """Initialize all session state variables"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = config["credentials"]["usernames"][st.session_state["username"]]["user_id"]
        st.session_state.session_id = generate_thread_id(st.session_state.user_id)
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hi — tell me what you'd like to do."}
        ]

    if "home_state" not in st.session_state:
        # Always fetch fresh state on initialization
        with st.spinner("Loading home state..."):
            home_state = await fetch_home_state(
                st.session_state["username"], 
            )
            st.session_state["home_state"] = home_state
            st.session_state["home_state_last_refresh"] = asyncio.get_event_loop().time()