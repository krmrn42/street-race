"""
Ollama Data Conversion Module

This module contains utilities for converting between the common message format
and Ollama-specific formats for API requests and responses.
"""

import json
from typing import Dict, List, Optional, Any, override

from llm.wrapper import (ContentPart, ContentPartText, ContentPartToolCall,
                      ContentPartToolResult, History, Message, Role)
from llm.history_converter import ChunkWrapper, HistoryConverter

_ROLES = {
    Role.SYSTEM: "system",
    Role.USER: "user",
    Role.MODEL: "assistant",
    Role.TOOL: "tool",
}

_OLLAMA_ROLES = {
    "system": Role.SYSTEM,
    "user": Role.USER,
    "assistant": Role.MODEL,
    "tool": Role.TOOL,
}


class OllamaResponseChunkWrapper(ChunkWrapper[Dict[str, Any]]):
    """
    Wrapper for Ollama's streaming response chunks that implements the ChunkWrapper interface.

    This allows for a consistent way to access content from Ollama's responses.
    """

    def __init__(self, chunk: Dict[str, Any]):
        super().__init__(chunk)

    @override
    def get_text(self) -> str:
        """Get text content from the chunk if it has message content."""
        if self.raw.get("message") and self.raw["message"].get("content"):
            return self.raw["message"]["content"]
        return ""

    @override
    def get_tool_calls(self) -> List[ContentPartToolCall]:
        """Get tool calls from the chunk if it has tool_calls."""
        tool_calls = []
        if self.raw.get("message") and self.raw["message"].get("tool_calls"):
            for tool_call in self.raw["message"]["tool_calls"]:
                tool_calls.append(
                    ContentPartToolCall(
                        id=tool_call.get("id", ""),
                        name=tool_call["function"]["name"],
                        arguments=json.loads(tool_call["function"]["arguments"]) 
                            if isinstance(tool_call["function"]["arguments"], str) 
                            else tool_call["function"]["arguments"]
                    )
                )
        return tool_calls


class OllamaConverter(HistoryConverter[Dict[str, Any], Dict[str, Any]]):
    """
    Handles conversion between common message format and Ollama-specific formats.

    This class centralizes all conversion logic to make code more maintainable
    and provide a clear data flow path.
    """

    def _from_content_part(self, part: ContentPart) -> Dict[str, Any]:
        """
        Convert a common format ContentPart to an Ollama-specific content part.

        Args:
            part: The common format content part to convert

        Returns:
            An Ollama-specific content part

        Raises:
            ValueError: If the content part type is not recognized
        """
        match part:
            case ContentPartText():
                return {"type": "text", "text": part.text}
            case ContentPartToolCall():
                return {
                    "type": "tool_call",
                    "id": part.id,
                    "function": {
                        "name": part.name,
                        "arguments": json.dumps(part.arguments) 
                            if isinstance(part.arguments, dict) 
                            else part.arguments
                    }
                }
            case ContentPartToolResult():
                return {
                    "type": "tool_result",
                    "tool_call_id": part.id,
                    "name": part.name,
                    "content": json.dumps(part.content) 
                        if isinstance(part.content, dict) 
                        else part.content
                }
            case _:
                raise ValueError(f"Unknown content type encountered {type(part)}: {part}")

    def from_history(self, history: History) -> List[Dict[str, Any]]:
        """
        Convert common History format to Ollama-specific message format.

        Args:
            history: The common format history

        Returns:
            List of Ollama-specific messages
        """
        provider_history: List[Dict[str, Any]] = []

        # Add system message if it exists
        if history.system_message:
            provider_history.append({
                "role": _ROLES[Role.SYSTEM],
                "content": history.system_message
            })

        # Add context as a user message if it exists
        if history.context:
            provider_history.append({
                "role": _ROLES[Role.USER],
                "content": history.context
            })

        # Convert each message in the conversation
        for message in history.conversation:
            if message.role == Role.MODEL:
                # Handle assistant messages with potential tool calls
                assistant_message = {"role": _ROLES[message.role]}
                
                content_parts = []
                tool_calls = []
                
                for part in message.content:
                    if isinstance(part, ContentPartText):
                        content_parts.append(part.text)
                    elif isinstance(part, ContentPartToolCall):
                        tool_calls.append({
                            "id": part.id,
                            "function": {
                                "name": part.name,
                                "arguments": json.dumps(part.arguments) 
                                    if isinstance(part.arguments, dict) 
                                    else part.arguments
                            }
                        })
                
                if content_parts:
                    assistant_message["content"] = " ".join(content_parts)
                
                if tool_calls:
                    assistant_message["tool_calls"] = tool_calls
                
                provider_history.append(assistant_message)
            
            elif message.role == Role.TOOL:
                # Handle tool messages
                for part in message.content:
                    if isinstance(part, ContentPartToolResult):
                        provider_history.append({
                            "role": _ROLES[message.role],
                            "tool_call_id": part.id,
                            "name": part.name,
                            "content": json.dumps(part.content) 
                                if isinstance(part.content, dict) 
                                else str(part.content)
                        })
            else:
                # Handle user and system messages
                text_parts = []
                for part in message.content:
                    if isinstance(part, ContentPartText):
                        text_parts.append(part.text)
                
                if text_parts:
                    provider_history.append({
                        "role": _ROLES[message.role],
                        "content": " ".join(text_parts)
                    })

        return provider_history

    def to_history(
        self,
        provider_history: List[Dict[str, Any]]
    ) -> List[Message]:
        """
        Convert Ollama-specific history to common format messages.

        Args:
            provider_history: The Ollama-specific history

        Returns:
            List of common format messages
        """
        if not provider_history:
            return []

        common_messages = []
        start_index = 0

        # Skip system message if it exists
        if provider_history and provider_history[0].get("role") == "system":
            start_index = 1
        
        # And skip the context message if it exists after the system message
        if len(provider_history) > start_index and provider_history[start_index].get("role") == "user":
            start_index += 1

        # Build a mapping of tool_call_ids to tool names
        tool_call_names = {}
        for message in provider_history:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                for tool_call in message.get("tool_calls"):
                    tool_call_names[tool_call.get("id", "")] = tool_call["function"]["name"]

        # Convert each message
        for message in provider_history[start_index:]:
            role = message.get("role")
            content = message.get("content", "")
            
            match role:
                case "user":
                    common_messages.append(
                        Message(
                            role=_OLLAMA_ROLES[role],
                            content=[ContentPartText(text=content)]
                        )
                    )
                case "assistant":
                    content_parts = []
                    
                    # Add text content if present
                    if content:
                        content_parts.append(ContentPartText(text=content))
                    
                    # Add tool calls if present
                    if message.get("tool_calls"):
                        for tool_call in message.get("tool_calls"):
                            arguments = tool_call["function"]["arguments"]
                            if isinstance(arguments, str):
                                try:
                                    arguments = json.loads(arguments)
                                except json.JSONDecodeError:
                                    # If not valid JSON, use as is
                                    pass
                                    
                            content_parts.append(
                                ContentPartToolCall(
                                    id=tool_call.get("id", ""),
                                    name=tool_call["function"]["name"],
                                    arguments=arguments
                                )
                            )
                    
                    common_messages.append(
                        Message(
                            role=_OLLAMA_ROLES[role],
                            content=content_parts
                        )
                    )
                case "tool":
                    # Handle tool result messages
                    tool_content = message.get("content", "{}")
                    if isinstance(tool_content, str):
                        try:
                            tool_content = json.loads(tool_content)
                        except json.JSONDecodeError:
                            # If not valid JSON, wrap in a dict
                            tool_content = {"result": tool_content}
                    
                    common_messages.append(
                        Message(
                            role=_OLLAMA_ROLES[role],
                            content=[
                                ContentPartToolResult(
                                    id=message.get("tool_call_id", ""),
                                    name=message.get("name", tool_call_names.get(message.get("tool_call_id", ""), "unknown")),
                                    content=tool_content
                                )
                            ]
                        )
                    )

        return common_messages

    def to_history_item(
        self,
        messages: List[OllamaResponseChunkWrapper] | List[ContentPartToolResult],
    ) -> Optional[Dict[str, Any]]:
        """
        Convert chunks or tool results to an Ollama-specific message.

        Args:
            messages: The chunks or tool results to convert

        Returns:
            An Ollama-specific message, or None if no valid message can be created
        """
        if not messages:
            return None

        if isinstance(messages[0], ContentPartToolResult):
            return self._tool_results_to_message(messages[0])
        else:
            return self._content_blocks_to_message(messages)

    def _content_blocks_to_message(
        self,
        messages: List[OllamaResponseChunkWrapper]
    ) -> Optional[Dict[str, Any]]:
        """
        Create an assistant message from content chunks.

        Args:
            chunks: The chunks to include in the message

        Returns:
            An assistant message with the content from all chunks
        """
        text_content = ""
        tool_calls = []

        for chunk in messages:
            if chunk.get_text():
                text_content += chunk.get_text()

            for tool_call in chunk.get_tool_calls():
                tool_calls.append({
                    "id": tool_call.id,
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments)
                            if isinstance(tool_call.arguments, dict)
                            else tool_call.arguments
                    }
                })

        # Create the message
        message = {"role": "assistant"}
        
        if text_content:
            message["content"] = text_content
            
        if tool_calls:
            message["tool_calls"] = tool_calls
            
        return message

    def _tool_results_to_message(
        self,
        result: ContentPartToolResult
    ) -> Optional[Dict[str, Any]]:
        """
        Create a tool results message from a tool result.

        Args:
            result: The tool result to include in the message

        Returns:
            A tool results message if valid, None otherwise
        """
        if not result:
            return None
            
        return {
            "role": "tool",
            "tool_call_id": result.id,
            "name": result.name,
            "content": json.dumps(result.content)
                if isinstance(result.content, dict)
                else str(result.content)
        }

    def create_chunk_wrapper(
        self,
        chunk: Dict[str, Any],
    ) -> ChunkWrapper[Dict[str, Any]]:
        """
        Create a wrapper for provider-specific streaming content chunks.

        Args:
            chunk: The chunk to wrap

        Returns:
            A ChunkWrapper[T] implementation to access chunk data
        """
        return OllamaResponseChunkWrapper(chunk)