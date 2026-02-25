import json
import logging
import os
from datetime import datetime

import redis
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="Smart Home Device Service", version="1.0.0")


class DeviceUpdate(BaseModel):
    status: dict


class Device(BaseModel):
    id: str
    status: dict


redis_client = redis.Redis(
    host=os.environ.get("REDIS_ENDPOINT"),
    port=os.environ.get("REDIS_PORT", 6379),
    decode_responses=True,
    username=os.environ.get("REDIS_USERNAME", "default"),
    password=os.environ.get("REDIS_PASSWORD"),
)


# This endpoint is used to initialize devices for a user from a JSON template
@app.post("/users/{user_id}/devices/initialize")
async def initialize_user_devices(user_id: str):
    """Initialize devices for a user from JSON template"""
    print("Initializing devices for user:", os.environ.get("HOME_TEMPLATE_PATH"))
    try:
        # Load devices from template for simplicity
        with open(os.environ.get("HOME_TEMPLATE_PATH")) as f:
            template = json.load(f)

        if not template:
            raise HTTPException(
                status_code=400,
                detail=f"Template {os.environ.get('HOME_TEMPLATE_PATH')} not found",
            )

        devices = template.get("devices", {})
        pipe = redis_client.pipeline()
        count = 0

        for room, room_devices in devices.items():
            for device_name, device_config in room_devices.items():
                key = f"user:{user_id}:device:{room}:{device_name}"

                # Create device state from template
                device_state = {
                    "id": f"{user_id}.{room}.{device_name}",
                    "user_id": user_id,
                    "room": room,
                    "name": device_name,
                    "status": device_config,
                    "is_online": True,
                    "last_updated": datetime.utcnow().isoformat(),
                }

                pipe.set(key, json.dumps(device_state))
                count += 1

        pipe.execute()

        return {
            "message": f"Initialized {count} devices for user {user_id}",
            "devices_count": count,
        }

    except redis.RedisError as e:
        logger.error(f"Redis error initializing user devices: {e}")
        raise HTTPException(status_code=503, detail="Redis connection failed")
    except Exception as e:
        logger.error(f"Error initializing devices for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize devices")


def get_device_key(user_id: str, room: str, device: str) -> str:
    return f"user:{user_id}:device:{room}:{device}"


def get_user_devices_pattern(user_id: str) -> str:
    return f"user:{user_id}:device:*"


def parse_device_key(key: str) -> tuple:
    """Parse 'user:123:device:room:name' -> (user_id, room, name)"""
    parts = key.split(":", 4)
    if len(parts) >= 5:
        return parts[1], parts[3], parts[4]
    return None, None, None


@app.get("/users/{user_id}/devices")
async def get_user_devices(user_id: str):
    """Get all devices for a specific user"""
    try:
        pattern = f"user:{user_id}:device:*"
        keys = redis_client.keys(pattern)
        devices = {}

        if keys:
            device_data = redis_client.mget(keys)

            for key, data in zip(keys, device_data):
                if data:
                    _, room, device_name = parse_device_key(key)
                    if room and device_name:
                        if room not in devices:
                            devices[room] = {}
                        devices[room][device_name] = json.loads(data)["status"]

        return devices
    except redis.RedisError as e:
        logger.error(f"Redis error getting user devices: {e}")
        raise HTTPException(status_code=503, detail="Redis connection failed")
    except Exception as e:
        logger.error(f"Error getting user devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user devices")


@app.get("/users/{user_id}/devices/{room}/{device}")
async def get_user_device(user_id: str, room: str, device: str):
    """Get specific device for a user"""
    try:
        key = get_device_key(user_id, room, device)
        data = redis_client.get(key)

        if not data:
            raise HTTPException(status_code=404, detail="Device not found")

        return json.loads(data)["status"]

    except redis.RedisError as e:
        logger.error(f"Redis error getting device: {e}")
        raise HTTPException(status_code=503, detail="Redis connection failed")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid device data")
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve device")


@app.put("/users/{user_id}/devices/{room}/{device}")
async def update_user_device(
    user_id: str, room: str, device: str, update: DeviceUpdate
):
    """Update device state for a specific user - used by agent"""
    try:
        key = get_device_key(user_id, room, device)
        current_data = redis_client.get(key)

        if not current_data:
            raise HTTPException(status_code=404, detail="Device not found")

        current_state = json.loads(current_data)

        # Update status and timestamp
        current_state["status"].update(update.status)
        current_state["last_updated"] = datetime.utcnow().isoformat()

        # Save to Redis
        redis_client.set(key, json.dumps(current_state))

        return current_state

    except redis.RedisError as e:
        logger.error(f"Redis error updating device: {e}")
        raise HTTPException(status_code=503, detail="Redis connection failed")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid device data")
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail="Failed to update device")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("🏠 Starting Smart Home Device Service...")
    print("📍 Service will be available at: http://localhost:8000")
    print("📖 API docs will be at: http://localhost:8000/docs")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
