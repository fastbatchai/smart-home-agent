import streamlit as st
import yaml
from pathlib import Path
from yaml.loader import SafeLoader
import time
from typing import Optional

@st.cache_data
def load_auth_config():
    """Load authentication configuration from YAML file"""

    root = Path(__file__).parent.parent.absolute()
    try:
        with open(f'{root}/config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except FileNotFoundError:
        st.error("Configuration file not found.")
        return None

def generate_thread_id(user_id: str, now: Optional[float] = None) -> str:

    if now is None:
        now = time.time()
    bucket = int(now // 600)
    return f"{user_id}_{bucket}"