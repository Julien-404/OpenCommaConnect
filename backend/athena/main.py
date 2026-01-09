import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://comma:password@postgres:5432/commaconnect")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", 8001))

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(title="Athena WebSocket Service")

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_metadata: Dict[str, dict] = {}

    async def connect(self, dongle_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[dongle_id] = websocket
        self.device_metadata[dongle_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat()
        }
        logger.info(f"Device {dongle_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, dongle_id: str):
        """Remove a WebSocket connection"""
        if dongle_id in self.active_connections:
            del self.active_connections[dongle_id]
        if dongle_id in self.device_metadata:
            del self.device_metadata[dongle_id]
        logger.info(f"Device {dongle_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, dongle_id: str, message: dict):
        """Send a message to a specific device"""
        if dongle_id in self.active_connections:
            try:
                await self.active_connections[dongle_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to {dongle_id}: {e}")
                self.disconnect(dongle_id)
                return False
        return False

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected devices"""
        disconnected = []
        for dongle_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {dongle_id}: {e}")
                disconnected.append(dongle_id)

        for dongle_id in disconnected:
            self.disconnect(dongle_id)

    def is_connected(self, dongle_id: str) -> bool:
        """Check if a device is connected"""
        return dongle_id in self.active_connections

manager = ConnectionManager()

# Redis client for pub/sub
redis_client = None

async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Athena WebSocket service starting...")
    await get_redis()
    logger.info("Athena WebSocket service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Athena WebSocket service shutting down...")
    if redis_client:
        await redis_client.close()
    logger.info("Athena WebSocket service stopped")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Athena WebSocket Service",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    try:
        r = await get_redis()
        await r.ping()
        redis_ok = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws/athena/{dongle_id}")
async def websocket_endpoint(websocket: WebSocket, dongle_id: str):
    """WebSocket endpoint for device connections"""
    await manager.connect(dongle_id, websocket)

    # Store connection in database
    # TODO: Add database recording of connection

    try:
        while True:
            # Receive message from device
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                logger.debug(f"Received from {dongle_id}: {message}")

                # Handle different message types
                if message.get("method") == "heartbeat":
                    # Update last heartbeat
                    manager.device_metadata[dongle_id]["last_heartbeat"] = datetime.utcnow().isoformat()

                    # Send heartbeat response
                    await manager.send_message(dongle_id, {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
                    })

                elif message.get("method") == "telemetry":
                    # Handle telemetry data
                    await handle_telemetry(dongle_id, message.get("params", {}))

                    # Acknowledge
                    await manager.send_message(dongle_id, {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {"status": "received"}
                    })

                elif message.get("method"):
                    # Handle JSON-RPC method call
                    result = await handle_rpc_method(dongle_id, message)
                    await manager.send_message(dongle_id, result)

                else:
                    # Unknown message format
                    logger.warning(f"Unknown message format from {dongle_id}: {message}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {dongle_id}: {data}")

    except WebSocketDisconnect:
        logger.info(f"Device {dongle_id} disconnected normally")
        manager.disconnect(dongle_id)

    except Exception as e:
        logger.error(f"Error in WebSocket connection for {dongle_id}: {e}")
        manager.disconnect(dongle_id)

async def handle_telemetry(dongle_id: str, params: dict):
    """Handle telemetry data from device"""
    # Store telemetry in Redis for real-time access
    r = await get_redis()
    await r.setex(f"telemetry:{dongle_id}", 60, json.dumps(params))

    # TODO: Store in database or forward to processing pipeline
    logger.debug(f"Telemetry from {dongle_id}: {params}")

async def handle_rpc_method(dongle_id: str, message: dict) -> dict:
    """Handle JSON-RPC method calls"""
    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")

    logger.info(f"RPC call from {dongle_id}: {method}")

    # Implement RPC methods
    if method == "getSystemInfo":
        # TODO: Get actual system info
        result = {
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat()
        }

    elif method == "takeSnapshot":
        # TODO: Implement snapshot request
        result = {
            "status": "requested",
            "snapshot_id": f"snap_{dongle_id}_{int(datetime.utcnow().timestamp())}"
        }

    elif method == "setDestination":
        # TODO: Implement navigation destination
        lat = params.get("lat")
        lon = params.get("lon")
        result = {
            "status": "destination_set",
            "lat": lat,
            "lon": lon
        }

    elif method == "reboot":
        # TODO: Implement reboot request
        result = {"status": "reboot_requested"}

    else:
        # Method not implemented
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": result
    }

@app.post("/send/{dongle_id}")
async def send_command(dongle_id: str, command: dict):
    """Send a command to a specific device (API endpoint for web frontend)"""
    if not manager.is_connected(dongle_id):
        return JSONResponse(
            status_code=404,
            content={"error": "Device not connected"}
        )

    success = await manager.send_message(dongle_id, command)

    if success:
        return {"status": "sent"}
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to send command"}
        )

@app.get("/connections")
async def list_connections():
    """List all active connections"""
    return {
        "connections": [
            {
                "dongle_id": dongle_id,
                "metadata": metadata
            }
            for dongle_id, metadata in manager.device_metadata.items()
        ],
        "total": len(manager.active_connections)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=WEBSOCKET_PORT)
