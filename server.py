#!/usr/bin/env python3
"""
WYGIWYH API MCP Server
Universal MCP server for the WYGIWYH expense tracking API

Copyright (c) 2025 ReNewator.com
All rights reserved.
"""

import os
import json
import base64
from typing import Any
import yaml
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl
import asyncio

API_BASE_URL = "https://your-WYGIWYH.com"

def get_auth_header() -> str:
    """Get the current Basic auth header from environment variables."""
    api_username = os.getenv("API_USERNAME", "")
    api_password = os.getenv("API_PASSWORD", "")
    
    if api_username and api_password:
        return base64.b64encode(f"{api_username}:{api_password}".encode()).decode()
    return ""

with open("attached_assets/WYGIWYH API (1)_1759581638933.yaml", "r", encoding="utf-8") as f:
    openapi_spec = yaml.safe_load(f)

app = Server("wygiwyh-api-server")

async def get_tools_list():
    """Get list of all tools (for HTTP transport)."""
    tools = generate_tools_from_openapi(openapi_spec)
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        for tool in tools
    ]

async def call_tool_internal(name: str, arguments: dict):
    """Call a tool directly (for HTTP transport)."""
    from mcp.types import TextContent
    # Call the existing call_tool function
    result = await call_tool(name, arguments)
    # Convert TextContent to dict
    if result:
        # Handle different result types
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, TextContent):
                return {"text": first_item.text}
        return {"text": str(result)}
    return {"error": "No response from tool"}

def convert_openapi_to_json_schema(schema: dict, components: dict) -> dict:
    """Convert OpenAPI schema to JSON Schema format for MCP tools."""
    if not schema:
        return {"type": "object", "properties": {}}
    
    result = {}
    
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")
        if ref_path[0] == "#" and ref_path[1] == "components" and ref_path[2] == "schemas":
            schema_name = ref_path[3]
            if schema_name in components.get("schemas", {}):
                return convert_openapi_to_json_schema(components["schemas"][schema_name], components)
    
    if "allOf" in schema:
        merged_properties = {}
        merged_required = []
        merged_type = None
        
        for sub_schema in schema["allOf"]:
            converted = convert_openapi_to_json_schema(sub_schema, components)
            if "properties" in converted:
                merged_properties.update(converted["properties"])
            if "required" in converted:
                merged_required.extend(converted["required"])
            if "type" in converted and not merged_type:
                merged_type = converted["type"]
        
        result["type"] = merged_type or "object"
        if merged_properties:
            result["properties"] = merged_properties
        if merged_required:
            result["required"] = list(set(merged_required))
        
        return result
    
    if "oneOf" in schema:
        return schema.get("oneOf", [{}])[0]
    
    if "type" in schema:
        result["type"] = schema["type"]
    
    if "properties" in schema:
        result["properties"] = {}
        for prop_name, prop_schema in schema["properties"].items():
            if not prop_schema.get("readOnly", False):
                result["properties"][prop_name] = convert_openapi_to_json_schema(prop_schema, components)
    
    if "required" in schema:
        result["required"] = [r for r in schema["required"] if r in result.get("properties", {})]
    
    for key in ["description", "title", "maxLength", "minLength", "maximum", "minimum", "pattern", "format", "nullable", "items", "enum"]:
        if key in schema:
            result[key] = schema[key]
    
    return result

def generate_tools_from_openapi(spec: dict) -> list[Tool]:
    """Generate MCP tools from OpenAPI specification."""
    tools = []
    paths = spec.get("paths", {})
    components = spec.get("components", {})
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                continue
            
            operation_id = operation.get("operationId", f"{method}_{path}")
            description = operation.get("description", operation.get("summary", f"{method.upper()} {path}"))
            
            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            if "parameters" in operation:
                for param in operation["parameters"]:
                    param_name = param["name"]
                    param_schema = convert_openapi_to_json_schema(param.get("schema", {"type": "string"}), components)
                    param_schema["description"] = param.get("description", "")
                    
                    if param["in"] == "path":
                        param_name = f"path_{param_name}"
                    elif param["in"] == "query":
                        param_name = f"query_{param_name}"
                    
                    input_schema["properties"][param_name] = param_schema
                    
                    if param.get("required", False):
                        input_schema["required"].append(param_name)
            
            if "requestBody" in operation:
                req_body = operation["requestBody"]
                content = req_body.get("content", {})
                
                body_schema = None
                preferred_content_type = None
                for content_type in ["application/json", "application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]:
                    if content_type in content:
                        body_schema = content[content_type].get("schema", {})
                        preferred_content_type = content_type
                        break
                
                if body_schema:
                    converted_schema = convert_openapi_to_json_schema(body_schema, components)
                    
                    if "properties" in converted_schema:
                        for prop_name, prop_schema in converted_schema["properties"].items():
                            input_schema["properties"][f"body_{prop_name}"] = prop_schema
                        
                        if "required" in converted_schema:
                            for req_field in converted_schema["required"]:
                                input_schema["required"].append(f"body_{req_field}")
            
            tool = Tool(
                name=operation_id,
                description=description[:1024],
                inputSchema=input_schema
            )
            
            tools.append(tool)
    
    return tools

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available API tools."""
    return generate_tools_from_openapi(openapi_spec)

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute API calls based on tool name and arguments."""
    
    auth_header = get_auth_header()
    if not auth_header:
        return [TextContent(
            type="text",
            text="Error: API_USERNAME and API_PASSWORD environment variables must be set to make API calls"
        )]
    
    paths = openapi_spec.get("paths", {})
    
    path = None
    method = None
    operation = None
    
    for api_path, path_item in paths.items():
        for http_method, op in path_item.items():
            if http_method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                continue
            if op.get("operationId") == name:
                path = api_path
                method = http_method.upper()
                operation = op
                break
        if path:
            break
    
    if not path or not method:
        return [TextContent(
            type="text",
            text=f"Error: Tool '{name}' not found in API specification"
        )]
    
    path_params = {}
    query_params = {}
    body_data = {}
    
    for key, value in arguments.items():
        if key.startswith("path_"):
            path_params[key[5:]] = value
        elif key.startswith("query_"):
            query_params[key[6:]] = value
        elif key.startswith("body_"):
            body_data[key[5:]] = value
    
    url = path
    for param_name, param_value in path_params.items():
        url = url.replace(f"{{{param_name}}}", str(param_value))
    
    full_url = f"{API_BASE_URL}{url}"
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(full_url, headers=headers, params=query_params)
            elif method == "POST":
                if body_data:
                    headers["Content-Type"] = "application/json"
                    response = await client.post(full_url, headers=headers, params=query_params, json=body_data)
                else:
                    response = await client.post(full_url, headers=headers, params=query_params)
            elif method == "PUT":
                if body_data:
                    headers["Content-Type"] = "application/json"
                    response = await client.put(full_url, headers=headers, params=query_params, json=body_data)
                else:
                    response = await client.put(full_url, headers=headers, params=query_params)
            elif method == "PATCH":
                if body_data:
                    headers["Content-Type"] = "application/json"
                    response = await client.patch(full_url, headers=headers, params=query_params, json=body_data)
                else:
                    response = await client.patch(full_url, headers=headers, params=query_params)
            elif method == "DELETE":
                response = await client.delete(full_url, headers=headers, params=query_params)
            else:
                return [TextContent(type="text", text=f"Error: Unsupported HTTP method: {method}")]
            
            response.raise_for_status()
            
            if response.status_code == 204:
                result = {"status": "success", "message": "Resource deleted or no content returned"}
            else:
                try:
                    result = response.json()
                except:
                    content_type = response.headers.get("content-type", "")
                    if "text/html" in content_type:
                        result = {
                            "status": "success",
                            "content_type": content_type,
                            "message": "Response received (HTML content)",
                            "text_preview": response.text[:500]
                        }
                    else:
                        result = {"response": response.text}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
    
    except httpx.HTTPStatusError as e:
        error_detail = ""
        status_code = e.response.status_code
        
        try:
            error_json = e.response.json()
            error_detail = json.dumps(error_json, indent=2)
        except:
            content_type = e.response.headers.get("content-type", "")
            if "text/html" in content_type:
                error_detail = f"HTML Error Page (status {status_code})"
                if e.response.text:
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', e.response.text, re.IGNORECASE)
                    if title_match:
                        error_detail += f"\nTitle: {title_match.group(1)}"
            else:
                error_detail = e.response.text[:500]
        
        return [TextContent(
            type="text",
            text=f"HTTP Error {status_code}:\n{error_detail}"
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {type(e).__name__}: {str(e)}"
        )]

async def main():
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
