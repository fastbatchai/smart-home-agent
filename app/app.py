# app.py
import asyncio
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from utils.agent import execute_agent
from utils.auth import load_auth_config
from utils.device import build_dashboard_html, device_icons
from utils.state import initialize_session_state

# Load CSS
with open(Path(__file__).parent / "static" / "styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page config
st.set_page_config(page_title="Smart Home Assistant", page_icon="🏠", layout="wide")
st.title("🏠 Smart Home Assistant")

# Authentication
config = load_auth_config()
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
_ = authenticator.login(location="sidebar", key="login")
if st.session_state["authentication_status"]:
    authenticator.logout("Logout", "sidebar")
    with st.sidebar:
        st.write(f"Welcome *{st.session_state['name']}*")
elif st.session_state["authentication_status"] == False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] == None:
    st.warning("Please enter your username and password")


# Initialize session state
asyncio.run(initialize_session_state(config))

# Device summary
device_counts = {}
total_on = 0
total_devices = 0

for room_data in st.session_state.home_state.values():
    for device_type, device_data in room_data.items():
        device_counts[device_type] = device_counts.get(device_type, 0) + 1
        total_devices += 1
        if device_data.get("state", 0):
            total_on += 1

summary_cols = st.columns([0.25, 0.25, 0.25, 0.25])

with summary_cols[0]:
    st.metric("Active Devices", f"{total_on}/{total_devices}")

for col_idx, (device_type, count) in enumerate(
    list(device_counts.items())[:3], start=1
):
    icon = device_icons.get(device_type, "⚡")
    with summary_cols[col_idx]:
        st.metric(f"{icon} {device_type.replace('_', ' ').title()}", count)

st.divider()

# Main Layout
col1, col2 = st.columns([0.45, 0.55])

# Left column - Home visualization
with col1:
    st.header("Devices")
    if not st.session_state.home_state:
        st.info("No devices found.")
    else:
        dashboard_html, dashboard_height = build_dashboard_html(
            st.session_state.home_state
        )
        components.html(dashboard_html, height=dashboard_height, scrolling=True)
    st.divider()


with col2:
    st.header("💬 Home Assistant")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything about your home"):
        with st.chat_message("human"):
            st.markdown(prompt)

        try:
            with st.spinner("Thinking..."):
                response = asyncio.run(
                    execute_agent(
                        message=prompt,
                        user_id=st.session_state.user_id,
                        user_name=st.session_state.username,
                        session_id=st.session_state.session_id,
                    )
                )
        except Exception as e:
            st.error(f"Failed to process request: {str(e)}")

        with st.chat_message("assistant"):
            st.markdown(response["response"])

        st.session_state.messages.append({"role": "human", "content": prompt})

        if "home_state" in response:
            st.session_state.home_state = response["home_state"]

        st.session_state.messages.append(
            {"role": "assistant", "content": response["response"]}
        )
        st.rerun()
