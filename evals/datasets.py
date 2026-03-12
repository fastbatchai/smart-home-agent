direct_commands_dataset = [
    (
        "h1",
        "Turn on the kitchen light.",
        {"kitchen": {"light": {"state": 1}}},
        ["direct_commands"],
    ),
    (
        "h2",
        "Turn off the living room light.",
        {"living_room": {"light": {"state": 0}}},
        ["direct_commands"],
    ),
    (
        "h2",
        "Turn on the TV",
        {"living_room": {"tv": {"state": 1}}},
        ["direct_commands"],
    ),
    (
        "h2",
        "Put on Netflix",
        {"living_room": {"tv": {"state": 1, "channel": "Netflix"}}},
        ["direct_commands"],
    ),
]

intent_resolution_dataset = [
    (
        "h1",
        "I just got home",
        {"entry": {"light": {"state": 1}}},
        ["intent_resolution"],
    ),
    (
        "h1",
        "Time to cook dinner",
        {"kitchen": {"light": {"state": 1}}},
        ["intent_resolution"],
    ),
    (
        "h3",
        "I'm going to sleep now",
        {"bedroom": {"light": {"state": 0}}},
        ["intent_resolution"],
    ),
    ("h3", "I'm bored", {"living_room": {"tv": {"state": 1}}}, ["intent_resolution"]),
    (
        "h3",
        "I want to relax",
        {"living_room": {"lamp": {"state": 1}}},
        ["intent_resolution"],
    ),
    (
        "h3",
        "The air feels stuffy",
        {"bedroom": {"air_purifier": {"state": 1}}},
        ["intent_resolution"],
    ),
]

device_resolution_dataset = [
    (
        "h3",
        "Turn on the dining room lamp",
        {"dining": {"lamp": {"state": 1}, "light": {"state": 0}}},
        ["device_resolution"],
    ),
    (
        "h3",
        "Turn on the dining room light",
        {"dining": {"light": {"state": 1}, "lamp": {"state": 0}}},
        ["device_resolution"],
    ),
    (
        "h3",
        "Turn on the living room lamp",
        {"living_room": {"lamp": {"state": 1}, "light": {"state": 1}}},
        ["device_resolution"],
    ),
    (
        "h3",
        "Play some music in the living room",
        {"living_room": {"sound_system": {"state": 1}, "tv": {"state": 0}}},
        ["device_resolution"],
    ),
    (
        "h3",
        "Turn on the lamp in the bedroom",
        {"bedroom": {"lamp": {"state": 1}, "light": {"state": 1}}},
        ["device_resolution"],
    ),
]

command_chaining_dataset = [
    (
        "h1",
        "Turn on the kitchen and dining lights",
        {"kitchen": {"light": {"state": 1}}, "dining": {"light": {"state": 1}}},
        ["command_chaining"],
    ),
    (
        "h1",
        "Turn off the bedroom light and turn on the kitchen light",
        {"bedroom": {"light": {"state": 0}}, "kitchen": {"light": {"state": 1}}},
        ["command_chaining"],
    ),
    (
        "h2",
        "Turn off the living room light and turn on the TV",
        {"living_room": {"light": {"state": 0}, "tv": {"state": 1}}},
        ["command_chaining"],
    ),
]

tool_selection_dataset = [
    # Action commands must call UpdateDevice
    ("h1", "Turn on the kitchen light", ["UpdateDevice"], [], ["tool_selection"]),
    (
        "h2",
        "Turn on the TV and set volume to 20",
        ["UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    # Query commands must call GetDeviceState, must NOT call UpdateDevice
    (
        "h2",
        "What is the current thermostat temperature?",
        [],
        ["UpdateDevice", "get_user_context"],
        ["tool_selection"],
    ),
    (
        "h1",
        "Is the bedroom light on?",
        [],
        ["UpdateDevice", "get_user_context"],
        ["tool_selection"],
    ),
    # Personalized/ambiguous commands should trigger get_user_context
    (
        "h2",
        "Set my preferred TV settings",
        ["get_user_context", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    # Multi-tool: query then conditionally update — must call both GetDeviceState and UpdateDevice
    (
        "h1",
        "Check if the kitchen light is off and turn it on if it is",
        ["GetDeviceState", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    (
        "h3",
        "Is the bedroom air purifier on? If not, turn it on.",
        ["GetDeviceState", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    # Multi-tool: personalized update — must call get_user_context and UpdateDevice
    (
        "h2",
        "Set up the living room using my preferred settings",
        ["get_user_context", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    (
        "h3",
        "Apply my bedtime routine",
        ["get_user_context", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
    # Multi-tool: query multiple devices — GetDeviceState called more than once
    (
        "h3",
        "What is the state of the bedroom light and the living room TV?",
        [],  # the agent has access to the home state so it doesn't need to call GetDeviceState
        ["UpdateDevice", "get_user_context"],
        ["tool_selection"],
    ),
    # Multi-tool: personalized query + update — all three tools
    (
        "h3",
        "Based on my preferences, adjust the living room for movie night",
        ["get_user_context", "GetDeviceState", "UpdateDevice"],
        [],
        ["tool_selection"],
    ),
]


agent_completion_datasets = [
    direct_commands_dataset,
    intent_resolution_dataset,
    device_resolution_dataset,
    command_chaining_dataset,
]
