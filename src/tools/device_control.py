from copy import deepcopy
from typing import Annotated, Any

from httpx import AsyncClient
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from src.config import config


@tool("GetDeviceState")
def get_device_state(
    state: Annotated[dict, InjectedState], device_name: str, room_name: str
) -> dict[str, str]:
    """
    returns the state a device in a room.
    """

    room_name = room_name.lower()
    device_name = device_name.lower()
    home_state = state["home_state"]
    if room_name not in home_state:
        return f"The room {room_name} does not exist. Here is the list of the room in the house {home_state.keys()}"
    if device_name not in home_state[room_name]:
        return f"The device {device_name} does not exist. Here is the list of devices in the room {room_name}: {home_state[room_name].keys()}"

    return home_state[room_name][device_name]


@tool("UpdateDevice")
async def update_device(
    state: Annotated[dict, InjectedState],
    device_name: str,
    room_name: str,
    new_device_info: dict[str, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Updates a device in a room.

    device_name is the name of the device to updated
    room_name is the name of the room where the device is updated
    new_device_info is the new updated device information. This should follow the same structure as in the home state
    """
    room_name = room_name.lower()
    device_name = device_name.lower()
    home_state = state["home_state"]

    if room_name not in home_state:
        return f"The room {room_name} does not exist. Here is the list of the room in the house {home_state.keys()}"
    if device_name not in home_state[room_name]:
        return f"The device {device_name} does not exist. Here is the list of devices in the room {room_name}: {home_state[room_name].keys()}"

    # check if the new device info follow the same struture, the LLM can provide any value and it is going to ovveride the current value
    # if it doesnt the initial structure, it will cause bugs
    if not isinstance(new_device_info, dict):
        return "The new device info should be a dictionary"

    if set(new_device_info.keys()) != set(home_state[room_name][device_name].keys()):
        return f"The new device info should follow the same structure as {home_state[room_name][device_name]}"

    # call the device service to update
    if config.TEST_MODE:
        updated_device = {"status": new_device_info}
    else:
        async with AsyncClient() as client:
            response = await client.put(
                f"{config.DEVICE_SERVICE_URL}/users/{state['user_name'].lower()}/devices/{room_name}/{device_name}",
                json={"status": new_device_info},
            )
            response.raise_for_status()
            updated_device = response.json()

    new_home_state = deepcopy(home_state)

    new_home_state[room_name][device_name] = updated_device["status"]

    return Command(
        update={
            "home_state": new_home_state,
            "messages": [
                ToolMessage(
                    f"Updated the state of the device {device_name} in the room {room_name} to {updated_device['status']}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


device_control_tools = [get_device_state, update_device]
