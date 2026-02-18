import time
from typing import Optional

from mem0 import MemoryClient

from src.config import config


def generate_thread_id(user_id: str, now: Optional[float] = None) -> str:
    """
    Combine the user_id with the current time bucket to create a thread ID.
    """
    if now is None:
        now = time.time()
    bucket = int(now // config.SESSION_WINDOW_SECONDS)

    return f"{user_id}_{bucket}"


def get_episodic_memory():
    client = MemoryClient(
        api_key=config.MEM0_API_KEY,
        org_id=config.MEM0_ORG_ID,
        project_id=config.MEM0_PROJECT_ID,
    )
    return client


long_term_memory = get_episodic_memory()
