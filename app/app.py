# app.py
from typing import Optional
import os
import streamlit as st
from typing import Dict, Any
import httpx
from yaml.loader import SafeLoader
from pathlib import Path
import streamlit_authenticator as stauth
from utils.auth import load_auth_config
from utils.state import initialize_session_state
from utils.device import device_icons, get_device_status
import asyncio

# # ---------- Layout ----------


# Load CSS
with open(Path(__file__).parent / 'static' / 'styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.set_page_config(page_title="Smart Home Assistant", page_icon="🏠", layout="wide")
st.title("🏠 Smart Home Assistant")
# Load config and initialize authentication
config = load_auth_config()
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Authentication UI
_ = authenticator.login(location='sidebar', key="login")
if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar')
    with st.sidebar:
        st.write(f'Welcome *{st.session_state["name"]}*')
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')


# Initialize state
asyncio.run(initialize_session_state(config))

# Center container for device summary
with st.container():
    # Add top divider
    
    # Centered header using markdown
    st.subheader("Device Summary")
    st.divider()

    # Device Summary section
    device_counts = {}
    total_on = 0
    total_devices = 0

    for room_data in st.session_state.home_state.values():
        for device_type, device_data in room_data.items():
            device_counts[device_type] = device_counts.get(device_type, 0) + 1
            total_devices += 1
            if device_data.get("state", 0):
                total_on += 1

    summary_cols = st.columns([0.25, 0.25, 0.25, 0.25])  # Equal width columns

    with summary_cols[0]:
        st.metric("Active Devices", f"{total_on}/{total_devices}")

    col_idx = 1
    for device_type, count in list(device_counts.items())[:3]:
        if col_idx < 4:
            icon = device_icons.get(device_type, "⚡")
            device_name = device_type.replace('_', ' ').title()
            with summary_cols[col_idx]:
                st.metric(f"{icon} {device_name}", count)
            col_idx += 1
    
    # Add bottom divider
    st.divider()

# Now create the main columns for home status and chat
col1, col2 = st.columns([0.45, 0.55])



# Create two columns


# Left column - Home visualization
with col1:
    st.header("Devices")
    # Create a grid for rooms (2 rooms per row)
    rooms = list(st.session_state.home_state.items())
    
    for i in range(0, len(rooms), 2):
        room_cols = st.columns(2)
        
        # First room
        room_name, room_data = rooms[i]
        room_display = room_name.replace('_', ' ').title()
        
        with room_cols[0]:
            with st.container():
                st.write(f"### 📍 {room_display}")
                
                # Display devices in this room
                for device_type, device_data in room_data.items():
                    icon = device_icons.get(device_type, "⚡")
                    device_name = device_type.replace('_', ' ').title()
                    status = get_device_status(device_type, device_data)
                    
                    if device_data.get("state", 0):
                        st.success(f"{icon} **{device_name}**  \n{status}")
                    else:
                        st.error(f"{icon} **{device_name}**  \n{status}")
        
        # Second room (if exists)
        if i + 1 < len(rooms):
            room_name, room_data = rooms[i + 1]
            room_display = room_name.replace('_', ' ').title()
            
            with room_cols[1]:
                with st.container():
                    st.write(f"### 📍 {room_display}")
                    
                    # Display devices in this room
                    for device_type, device_data in room_data.items():
                        icon = device_icons.get(device_type, "⚡")
                        device_name = device_type.replace('_', ' ').title()
                        status = get_device_status(device_type, device_data)
                        
                        if device_data.get("state", 0):
                            st.success(f"{icon} **{device_name}**  \n{status}")
                        else:
                            st.error(f"{icon} **{device_name}**  \n{status}")
    
    st.divider()

async def execute_agent_command(
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
                "session_id": session_id
            }
        )
        response.raise_for_status()
        return response.json().get("response", {})


with col2:
    st.header("💬 Chat Assistant")
    
    # Chat input
    # user_input = st.text_input("Type your message:", placeholder="Ask me anything about your home...")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"]) 
        
    if prompt := st.chat_input("Ask me anything about your home"):

        # Display user message in chat message container
        st.chat_message("human").markdown(prompt)

      
        # Display assistant response in chat message container
        try:
            with st.spinner("Processing your request..."):
                response = asyncio.run(execute_agent_command(
                        message=prompt,
                        user_id=st.session_state.user_id,
                        user_name=st.session_state.username,
                        session_id=st.session_state.session_id
                ))
        except Exception as e:
            st.error(f"Failed to process request: {str(e)}")

        with st.chat_message("assistant"):
            st.markdown(response["response"])

        st.session_state.messages.append({"role": "human", "content": prompt})
        
        if "home_state" in response:
            st.session_state.home_state = response["home_state"]
                    
        st.session_state.messages.append({"role": "assistant", "content": response["response"]})
        st.rerun()