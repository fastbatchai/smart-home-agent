from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
import uvicorn
from typing import Any

from src.response_endpoint import execute_agent

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Smarthome Agent API")


class QueryRequest(BaseModel):
    message: str
    user_id: str
    user_name: str
    session_id: str

class AgentResponse(BaseModel):
    response: str
    home_state: dict[str, Any]

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/agent/query")
async def handle_query(request: QueryRequest):
    print(request)
    try: 
        response = await execute_agent(
        messages=request.message,
        user_id=request.user_id,
        user_name=request.user_name,
        session_id=request.session_id,
    )
        response = AgentResponse(response=response[0], home_state=response[1])
        logger.info(f"Agent response: {response}")
        return {"response": response}
    except Exception as e: 
        error_msg = f"Error processing query: {str(e)}"
        logger.error(error_msg, exc_info=True)  # Log the full exception
        return HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    print("🏠 Starting Smart Home Agent...")
    print("📍 Service will be available at: http://localhost:8001")
    print("📖 API docs will be at: http://localhost:8001/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")