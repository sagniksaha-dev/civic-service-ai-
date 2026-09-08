import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.schemas.chat import ChatQueryRequest
from app.services.chat_service import chat_service
from app.websocket.manager import connection_manager

ws_router = APIRouter()


@ws_router.websocket("/ws/chat")
@ws_router.websocket("/api/v1/chat/ws")
async def websocket_chat_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """
    Real-time bidirectional WebSocket endpoint for civic assistant interactions.
    Payload format:
    {
        "type": "message",
        "question": "What documents are required for a water connection?",
        "session_id": "optional-uuid",
        "token": "optional-jwt-token",
        "department_id": null,
        "service_id": null
    }
    """
    conn_id = client_id or str(uuid.uuid4())
    await connection_manager.connect(websocket, conn_id)

    # Send initial connection acknowledgment
    await connection_manager.send_json({
        "type": "connected",
        "connection_id": conn_id,
        "message": "Connected to Civic Assistant Real-time Service"
    }, conn_id)

    db: Session = SessionLocal()
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await connection_manager.send_json({
                    "type": "error",
                    "error": "Invalid JSON format"
                }, conn_id)
                continue

            msg_type = data.get("type", "message")

            # Handle ping/heartbeat
            if msg_type == "ping":
                await connection_manager.send_json({"type": "pong"}, conn_id)
                continue

            if msg_type == "message":
                question = data.get("question", "").strip()
                if not question:
                    await connection_manager.send_json({
                        "type": "error",
                        "error": "Question field cannot be empty"
                    }, conn_id)
                    continue

                session_id = data.get("session_id")
                token = data.get("token")
                user_id = None

                # Optional user token resolution
                if token:
                    payload = decode_access_token(token)
                    if payload and payload.get("sub"):
                        try:
                            user_id = int(payload["sub"])
                        except ValueError:
                            user_id = None

                # 1. Emit typing indicator
                await connection_manager.send_json({
                    "type": "typing",
                    "status": True,
                    "session_id": session_id
                }, conn_id)

                # 2. Process through Grounded RAG
                try:
                    query_req = ChatQueryRequest(
                        question=question,
                        session_id=session_id,
                        department_id=data.get("department_id"),
                        service_id=data.get("service_id")
                    )
                    rag_res = chat_service.process_query(db=db, query_in=query_req, user_id=user_id)

                    # 3. Send structured response
                    await connection_manager.send_json({
                        "type": "answer",
                        "session_id": rag_res.session_id,
                        "question": rag_res.question,
                        "answer": rag_res.answer,
                        "sources": [s.model_dump() for s in rag_res.sources],
                        "disclaimer": rag_res.disclaimer,
                        "is_grounded": rag_res.is_grounded
                    }, conn_id)
                except Exception as e:
                    logger.error("Error processing WebSocket query: %s", e)
                    await connection_manager.send_json({
                        "type": "error",
                        "error": f"Failed to process inquiry: {str(e)}"
                    }, conn_id)

    except WebSocketDisconnect:
        connection_manager.disconnect(conn_id)
    except Exception as e:
        logger.error("WebSocket unhandled exception for %s: %s", conn_id, e)
        connection_manager.disconnect(conn_id)
    finally:
        db.close()
