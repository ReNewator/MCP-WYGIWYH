#!/usr/bin/env python3
"""
MCP Server with HTTP Streamable transport for n8n

Copyright (c) 2025 ReNewator.com
All rights reserved.
"""

import os
import secrets
import json
from typing import Any
from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
import uvicorn
from server import app as mcp_server, get_tools_list

MCP_TOKEN = os.getenv("MCP_TOKEN", "")

if not MCP_TOKEN:
    MCP_TOKEN = secrets.token_urlsafe(32)
    print(f"\n{'='*60}")
    print("WARNING: MCP_TOKEN not set!")
    print(f"Generated temporary token: {MCP_TOKEN}")
    print("Set MCP_TOKEN environment variable")
    print(f"{'='*60}\n")

def check_bearer_token(request: Request) -> bool:
    """Check if Bearer token is valid."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    try:
        token = auth_header.split(" ")[1]
        return token == MCP_TOKEN
    except:
        return False

async def health_check(request: Request):
    """Health check endpoint - no auth required."""
    return JSONResponse({
        "status": "ok",
        "server": "WYGIWYH MCP Server",
        "transport": "HTTP Streamable",
        "auth": "Bearer token required for MCP endpoints"
    })

async def handle_root_get(request: Request):
    """Handle GET requests to root - return SSE stream for initialization."""
    if not check_bearer_token(request):
        return Response(
            content='{"error": "Unauthorized"}',
            status_code=401,
            media_type="application/json",
            headers={"WWW-Authenticate": 'Bearer realm="MCP Server"'}
        )
    
    print(f"SSE connection from {request.client}")
    
    # Return SSE stream with server info
    async def event_stream():
        # Send initialize event
        yield f"event: message\n"
        yield f"data: {json.dumps({'jsonrpc': '2.0', 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'serverInfo': {'name': 'WYGIWYH MCP Server', 'version': '1.0.0'}}})}\n\n"
        
        # Keep connection alive
        import asyncio
        while True:
            await asyncio.sleep(30)
            yield f": keepalive\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def handle_root_post(request: Request):
    """Handle POST requests to root - execute MCP methods."""
    if not check_bearer_token(request):
        return Response(
            content='{"error": "Unauthorized"}',
            status_code=401,
            media_type="application/json",
            headers={"WWW-Authenticate": 'Bearer realm="MCP Server"'}
        )
    
    try:
        body = await request.json()
        print(f"Received JSON-RPC request: {body.get('method', 'unknown')}")
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle notifications (no id, no response needed)
        if request_id is None:
            print(f"Notification received: {method}")
            # Notifications don't get a response, just return 200
            return Response(status_code=200)
        
        # Handle different MCP methods
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "WYGIWYH MCP Server",
                    "version": "1.0.0"
                }
            }
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })
        
        elif method == "tools/list":
            # Get tools from the MCP server
            tools_list = await get_tools_list()
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            })
        
        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            print(f"Calling tool: {tool_name} with args: {tool_args}")
            
            # Call the tool using the MCP server
            from server import call_tool_internal
            result = await call_tool_internal(tool_name, tool_args)
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result)
                        }
                    ]
                }
            })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=400)
    
    except Exception as e:
        print(f"Error handling request: {e}")
        import traceback
        traceback.print_exc()
        
        error_request_id = None
        try:
            body_dict = await request.json()
            error_request_id = body_dict.get("id")
        except:
            pass
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": error_request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status_code=500)

routes = [
    Route("/", handle_root_get, methods=["GET"]),
    Route("/", handle_root_post, methods=["POST"]),
    Route("/health", health_check, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]

app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting WYGIWYH MCP Server with HTTP Streamable")
    print("="*60)
    print(f"Server: http://0.0.0.0:5000")
    print(f"Token: {MCP_TOKEN[:8]}...{MCP_TOKEN[-4:]}")
    print("\nEndpoints:")
    print("  GET  / - SSE stream for MCP")
    print("  POST / - JSON-RPC MCP methods")
    print("  GET  /health - Health check (no auth)")
    print("\nn8n Configuration:")
    print("  HTTP Streamable URL: https://your-domain/")
    print("  Additional Headers: Authorization:Bearer " + MCP_TOKEN)
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
