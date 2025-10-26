# openai agent with mcp integration
# handles conversation, tool calls, and mcp server communication

import asyncio
import json
from typing import List, Dict, Any, Callable, Optional
from openai import AsyncOpenAI
from mcp_bridge import MCPBridge


class OpenAIMCPAgent:
    """
    openai-powered agent that uses mcp tools
    
    workflow:
    1. user sends message
    2. openai decides which tools to call
    3. agent calls tools via mcp bridge
    4. openai synthesizes final response
    """
    
    def __init__(self, sdk_name: str, openai_api_key: str):
        self.sdk_name = sdk_name
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.bridge = None
        self.tools = []
        self.conversation_history = []
        self.model = "gpt-4-turbo-preview"
        self.tool_name_map = {}  # maps openai names to mcp names
        self.system_prompt = ""  # built after tools are loaded
        self.tools_truncated = 0  # count of tools not loaded due to OpenAI limit
        
    def _build_system_prompt(self) -> str:
        """create system prompt for the agent"""
        # build tool summary
        tool_categories = {}
        for tool in self.tools:
            parts = tool['function']['name'].split('_')
            category = parts[0] if parts else 'other'
            tool_categories[category] = tool_categories.get(category, 0) + 1
        
        tool_summary = ", ".join([f"{count} {cat} tools" for cat, count in sorted(tool_categories.items())[:5]])
        
        truncation_notice = ""
        if self.tools_truncated > 0:
            truncation_notice = f"\nNOTE: {self.tools_truncated} additional tools exist but aren't loaded due to OpenAI's 128 tool limit."
        
        return f"""you are an expert assistant with access to the {self.sdk_name} python sdk.

IMPORTANT - YOUR CAPABILITIES:
- you have {len(self.tools)} tools available from the {self.sdk_name} SDK{truncation_notice}
- tool categories: {tool_summary}
- you can ONLY use tools from the {self.sdk_name} SDK
- if the user asks about something outside this SDK's scope, politely explain what you CAN help with

WORKFLOW:
1. check if the request matches your available tools
2. if yes: choose the right tool(s) and execute
3. if no: explain your SDK's capabilities and what you CAN do instead

GUIDELINES:
- be direct and helpful
- use tools immediately for read operations (list, get, read, describe)
- explain what tool you're calling and why
- format results clearly (use lists/tables when helpful)
- if something fails, suggest alternatives using your available tools
- for dangerous operations (delete, update, create), explain the action first

EXAMPLE RESPONSES:
[OK] Good: "I'll use {self.sdk_name}.list_pods() to check the pods..."
[OK] Good: "This requires OS filesystem access, which isn't available in the {self.sdk_name} SDK. I can help you with: [list your capabilities]"
[FAIL] Bad: "I don't have access to that" (too vague - explain what you DO have)

remember: you are specifically a {self.sdk_name} expert with exactly {len(self.tools)} tools at your disposal."""
    
    async def initialize(self):
        """initialize mcp connection and load tools"""
        try:
            # create bridge to mcp server
            self.bridge = MCPBridge(self.sdk_name)
            await self.bridge.start()
            
            # fetch available tools
            tools_response = await self.bridge.list_tools()
            
            if not tools_response or "tools" not in tools_response:
                raise RuntimeError(
                    f"Invalid response from MCP server\n"
                    f"Expected 'tools' key but got: {tools_response}"
                )
            
            # convert to openai function format and build name mapping
            all_tools = []
            for tool in tools_response.get("tools", []):
                openai_tool = self._convert_to_openai_tool(tool)
                all_tools.append(openai_tool)
                
                # map openai name to mcp name
                openai_name = openai_tool["function"]["name"]
                mcp_name = tool["name"]
                self.tool_name_map[openai_name] = mcp_name
            
            if not all_tools:
                raise RuntimeError(
                    f"No tools found for SDK '{self.sdk_name}'\n"
                    f"The SDK may not have any discoverable methods"
                )
            
            # OpenAI has a hard limit of 128 tools per request
            # If we have more, take the first 128 and warn the user
            OPENAI_MAX_TOOLS = 128
            if len(all_tools) > OPENAI_MAX_TOOLS:
                self.tools = all_tools[:OPENAI_MAX_TOOLS]
                self.tools_truncated = len(all_tools) - OPENAI_MAX_TOOLS
            else:
                self.tools = all_tools
                self.tools_truncated = 0
            
            # NOW build system prompt (after tools are loaded)
            self.system_prompt = self._build_system_prompt()
            
            # initialize conversation with system prompt
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
            
        except Exception as e:
            # cleanup on failure
            if self.bridge:
                try:
                    await self.bridge.stop()
                except:
                    pass
            raise RuntimeError(
                f"Failed to initialize agent for SDK '{self.sdk_name}'\n"
                f"Error: {str(e)}"
            ) from e
    
    async def process(
        self,
        user_message: str,
        on_tool_call: Optional[Callable] = None
    ) -> str:
        """
        process user message and return response
        
        args:
            user_message: user's input
            on_tool_call: callback(tool_name, args) -> tool_display widget
        
        returns:
            agent's response
        """
        # add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # agent loop: may call tools multiple times
        max_iterations = 5
        for iteration in range(max_iterations):
            # call openai
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
            )
            
            message = response.choices[0].message
            
            # if no tool calls, we're done
            if not message.tool_calls:
                # add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content
                })
                return message.content
            
            # agent wants to call tools
            # add assistant message (with tool calls) to history
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # execute tool calls
            for tool_call in message.tool_calls:
                openai_tool_name = tool_call.function.name
                
                # convert openai name back to mcp name
                mcp_tool_name = self.tool_name_map.get(openai_tool_name, openai_tool_name)
                
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                
                # notify ui (if callback provided)
                tool_display = None
                if on_tool_call:
                    tool_display = await on_tool_call(mcp_tool_name, arguments)
                
                # call tool via mcp
                try:
                    result = await self.bridge.call_tool(mcp_tool_name, arguments)
                    result_str = self._format_tool_result(result)
                    
                    # update ui
                    if tool_display:
                        tool_display.set_result(result_str)
                    
                    # add tool result to history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": openai_tool_name,  # use openai name for conversation history
                        "content": result_str
                    })
                    
                except Exception as e:
                    error_msg = f"error calling {mcp_tool_name}: {str(e)}"
                    
                    # update ui
                    if tool_display:
                        tool_display.set_error(str(e))
                    
                    # add error to history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": openai_tool_name,  # use openai name for conversation history
                        "content": error_msg
                    })
            
            # continue loop to let openai synthesize response
        
        # if we hit max iterations, return explanation
        return "i've made multiple tool calls but need to stop here. please review the results above."
    
    def _convert_to_openai_tool(self, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """convert mcp tool schema to openai function calling format"""
        # openai requires:
        # 1. tool names to match ^[a-zA-Z0-9_-]+$
        # 2. tool names to be <=64 characters
        
        mcp_name = mcp_tool["name"]
        openai_name = mcp_name.replace(".", "_")
        
        # OpenAI has a 64 character limit for function names
        OPENAI_MAX_NAME_LENGTH = 64
        if len(openai_name) > OPENAI_MAX_NAME_LENGTH:
            # For long names, use smart truncation:
            # Take first 54 chars + "_" + 8-char hash of full name
            # This keeps names readable while ensuring uniqueness
            import hashlib
            name_hash = hashlib.md5(openai_name.encode()).hexdigest()[:8]
            openai_name = openai_name[:54] + "_" + name_hash
        
        return {
            "type": "function",
            "function": {
                "name": openai_name,
                "description": mcp_tool.get("description", "no description available"),
                "parameters": mcp_tool.get("inputSchema", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
        }
    
    def _format_tool_result(self, result: Any) -> str:
        """format tool result for context"""
        if result is None:
            return "null"
        
        # try to serialize to json
        try:
            result_str = json.dumps(result, indent=2, default=str)
        except Exception:
            result_str = str(result)
        
        # truncate if too long (openai context limits)
        max_length = 4000
        if len(result_str) > max_length:
            return result_str[:max_length] + f"\n... (truncated from {len(result_str)} chars)"
        
        return result_str
    
    async def cleanup(self):
        """cleanup resources"""
        if self.bridge:
            await self.bridge.stop()

