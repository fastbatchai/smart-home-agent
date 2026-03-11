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
    "lock": "🔒",
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
        return (
            f"{device_data.get('temperature', 0)}°F ({device_data.get('mode', 'off')})"
        )

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


def build_dashboard_html(home_state: dict) -> tuple[str, int]:
    rooms = list(home_state.items())

    html = """
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: transparent; padding: 4px; }
    </style>
    <div style="columns: 2; column-gap: 16px;">
    """

    for room_name, room_data in rooms:
        room_display = room_name.replace("_", " ").title()
        html += f"""
        <div style="break-inside: avoid; margin-bottom: 16px;">
            <p style="font-size:0.78rem; font-weight:600; text-transform:uppercase;
                      letter-spacing:0.8px; color:#4a5270; border-bottom:2px solid #e8eaf0;
                      padding-bottom:6px; margin-bottom:8px;">
                📍 {room_display}
            </p>
        """
        for device_type, device_data in room_data.items():
            icon = device_icons.get(device_type, "⚡")
            device_name = device_type.replace("_", " ").title()
            status = get_device_status(device_type, device_data)
            is_on = bool(device_data.get("state", 0))

            border_color = "#22c55e" if is_on else "#e2e5ef"
            icon_bg = "#f0fdf4" if is_on else "#f5f6fa"
            dot_color = "#22c55e" if is_on else "#cbd5e1"
            dot_shadow = "box-shadow:0 0 0 3px #dcfce7;" if is_on else ""

            html += f"""
            <div style="background:#fff; border-radius:10px; padding:12px 14px;
                        margin-bottom:8px; border:1px solid #e8eaf0;
                        border-left:3px solid {border_color};
                        display:flex; align-items:center; gap:12px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="font-size:1.3rem; width:36px; height:36px;
                            display:flex; align-items:center; justify-content:center;
                            border-radius:8px; background:{icon_bg}; flex-shrink:0;">
                    {icon}
                </div>
                <div style="flex:1; min-width:0;">
                    <div style="font-size:0.82rem; font-weight:600; color:#1a1d2e;">
                        {device_name}
                    </div>
                    <div style="font-size:0.73rem; color:#8891a8; margin-top:1px;
                                font-family:'DM Mono',monospace;">
                        {status}
                    </div>
                </div>
                <div style="width:8px; height:8px; border-radius:50%;
                            background:{dot_color}; flex-shrink:0; {dot_shadow}">
                </div>
            </div>
            """
        html += "</div>"

    html += "</div>"

    total_devices = sum(len(d) for _, d in rooms)
    height = (total_devices * 60) + (len(rooms) * 50) + 20
    return html, height
