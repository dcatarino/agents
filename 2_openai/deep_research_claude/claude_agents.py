import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel
import anthropic
from anthropic import AsyncAnthropic

T = TypeVar('T', bound=BaseModel)

class Tool(ABC):
    """Base class for tools that agents can use"""
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass

class WebSearchTool:
    """Tool for performing web searches using Anthropic's native web search"""
    
    def __init__(self, search_context_size: str = "medium"):
        self.search_context_size = search_context_size
        self.max_uses = {"low": 3, "medium": 5, "high": 8}.get(search_context_size, 5)
    
    def get_tool_definition(self) -> dict:
        """Get the tool definition for Anthropic's web search"""
        return {
            "type": "web_search",
            "web_search": {
                "max_uses": self.max_uses
            }
        }

class ClaudeAgent:
    """Claude-based agent that can use tools and generate structured outputs"""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "claude-3-5-sonnet-20241022",
        tools: Optional[List[Union[Tool, WebSearchTool]]] = None,
        output_type: Optional[Type[BaseModel]] = None,
        max_tokens: int = 4000
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self.output_type = output_type
        self.max_tokens = max_tokens
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def run(self, input_text: str) -> Union[str, BaseModel]:
        """Run the agent with the given input"""
        messages = [
            {
                "role": "user",
                "content": f"{self.instructions}\n\nInput: {input_text}"
            }
        ]
        
        # Prepare tools for Anthropic API
        tools_config = []
        for tool in self.tools:
            if isinstance(tool, WebSearchTool):
                tools_config.append(tool.get_tool_definition())
            elif hasattr(tool, 'get_name'):
                # Custom function tool
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": tool.get_name(),
                        "description": tool.get_description()
                    }
                })
        
        # If we have tools, use them
        if tools_config:
            return await self._run_with_native_tools(messages, tools_config)
        else:
            return await self._run_simple(messages)
    
    async def _run_simple(self, messages: List[Dict[str, str]]) -> Union[str, BaseModel]:
        """Run agent without tools"""
        if self.output_type:
            # Add structured output instructions
            schema = self.output_type.model_json_schema()
            messages[0]["content"] += f"\n\nPlease respond with a JSON object that matches this schema:\n{json.dumps(schema, indent=2)}"
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages
        )
        
        content = response.content[0].text
        
        if self.output_type:
            try:
                # Try to extract JSON from the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    return self.output_type(**data)
                else:
                    # Fallback: try to parse the entire content as JSON
                    data = json.loads(content)
                    return self.output_type(**data)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse structured output: {e}")
                return content
        
        return content
    
    async def _run_with_native_tools(self, messages: List[Dict[str, str]], tools_config: List[Dict]) -> str:
        """Run agent with Anthropic's native tools"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            tools=tools_config
        )
        
        # Claude will handle web search automatically and include results in the response
        content = response.content[0].text if response.content else "No response generated"
        return content

class Runner:
    """Runner class to execute agents"""
    
    @staticmethod
    async def run(agent: ClaudeAgent, input_text: str) -> 'RunResult':
        """Run an agent and return the result"""
        output = await agent.run(input_text)
        return RunResult(final_output=output)

class RunResult:
    """Result of running an agent"""
    
    def __init__(self, final_output: Any):
        self.final_output = final_output
    
    def final_output_as(self, output_type: Type[T]) -> T:
        """Convert final output to specified type"""
        if isinstance(self.final_output, output_type):
            return self.final_output
        elif isinstance(self.final_output, dict):
            return output_type(**self.final_output)
        else:
            raise ValueError(f"Cannot convert {type(self.final_output)} to {output_type}")

# Simple tracing functions (placeholders)
def gen_trace_id() -> str:
    """Generate a trace ID"""
    import uuid
    return str(uuid.uuid4())

def trace(name: str, trace_id: str = None):
    """Trace context manager"""
    class TraceContext:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return TraceContext()

# Function tool decorator
def function_tool(func):
    """Decorator to create a function tool"""
    class FunctionTool(Tool):
        def get_name(self) -> str:
            return func.__name__
        
        def get_description(self) -> str:
            return func.__doc__ or f"Execute {func.__name__}"
        
        async def execute(self, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(**kwargs)
            else:
                return func(**kwargs)
    
    return FunctionTool()