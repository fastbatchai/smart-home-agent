device_icons = {
    "light": "💡",
    "thermostat": "🌡️",
    "tv": "📺",
    "air_conditioner": "❄️",
    "fan": "🌀",
    "door": "🚪",
    "window": "🪟",
    "camera": "📹",
    "speaker": "🔊",
    "lock": "🔒"
}

def get_device_status(device_type, device_data):
    """Generate status text for different device types"""
    
    device_type = device_type.lower()
    
    if device_type == "light":
        if device_data.get("state", 0):
            return f"ON ({device_data.get('brightness', 100)}%, {device_data.get('color', 'white')})"
        else:
            return "OFF"
    
    elif device_type == "thermostat":
        return f"{device_data.get('temperature', 0)}°C → {device_data.get('target_temperature', 0)}°C ({device_data.get('mode', 'off')})"
    
    elif device_type == "tv":
        if device_data.get("state", 0):
            return f"ON (Vol: {device_data.get('volume', 0)}, Ch: {device_data.get('channel', 1)})"
        else:
            return "OFF"
    
    elif device_type == "air_conditioner":
        if device_data.get("state", 0):
            return f"ON ({device_data.get('temperature', 20)}°C, {device_data.get('mode', 'cool')})"
        else:
            return "OFF"
    
    elif device_type == "fan":
        if device_data.get("state", 0):
            return f"ON (Speed: {device_data.get('speed', 1)})"
        else:
            return "OFF"
    
    else:
        # Generic device status
        if device_data.get("state", 0):
            return "ON"
        else:
            return "OFF"