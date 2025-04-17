"""
Gemini Data Conversion Module

This module contains utilities for converting between the common message format
and Gemini-specific formats for API requests and responses.
"""

from typing import List, Optional, override

from google.genai import types

from streetrace.llm.history_converter import ChunkWrapper, HistoryConverter
from streetrace.llm.wrapper import (
    ContentPart,
    ContentPartText,
    ContentPartToolCall,
    ToolCallResult,
    ContentPartToolResult,
    History,
    Message,
)


class GenerateContentPartWrapper(ChunkWrapper[types.Part]):
    """
    Wrapper for Gemini's Part that implements the ChunkWrapper interface.

    This allows for a consistent way to access content from Gemini's responses.
    """

    def __init__(self, chunk: types.Part):
        super().__init__(chunk)

    @override
    def get_text(self) -> str:
        """Get text content from the chunk if it has text."""
        return self.raw.text or ""

    @override
    def get_tool_calls(self) -> List[ContentPartToolCall]:
        """Get tool calls from the chunk if it has function calls."""
        return (
            [
                ContentPartToolCall(
                    id=self.raw.function_call.id,
                    name=self.raw.function_call.name,
                    arguments=self.raw.function_call.args,
                )
            ]
            if self.raw.function_call
            else []
        )

    @override
    def get_finish_message(self) -> str:
        """Get finish message if this is the final chunk from the model."""
        return None


class GeminiConverter(HistoryConverter[types.Content, types.Part]):
    """
    Handles conversion between common message format and Gemini-specific formats.

    This class centralizes all conversion logic to make code more maintainable
    and provide a clear data flow path.
    """

    def _from_content_part(self, part: ContentPart) -> types.Part:
        """
        Convert a common format ContentPart to a Gemini-specific part.

        Args:
            part: The common format content part to convert

        Returns:
            A Gemini-specific part

        Raises:
            ValueError: If the content part type is not recognized
        """
        match part:
            case ContentPartText():
                return types.Part.from_text(text=part.text)
            case ContentPartToolCall():
                return types.Part.from_function_call(
                    name=part.name, args=part.arguments
                )
            case ContentPartToolResult():
                return types.Part.from_function_response(
                    name=part.name, response=part.content.model_dump()
                )
            case _:
                raise ValueError(
                    f"Unknown content type encountered {type(part)}: {part}"
                )

    def _to_content_part(self, part: types.Part) -> ContentPart:
        """
        Convert a Gemini-specific part to common format ContentPart.

        Args:
            part: The Gemini-specific part to convert

        Returns:
            A common format ContentPart

        Raises:
            ValueError: If the content type is not recognized
        """
        if part.text:
            return ContentPartText(text=part.text)
        elif part.function_call:
            return ContentPartToolCall(
                id=part.function_call.id,
                name=part.function_call.name,
                arguments=part.function_call.args,
            )
        elif part.function_response:
            return ContentPartToolResult(
                id=part.function_response.id,
                name=part.function_response.name,
                content=ToolCallResult.model_validate(part.function_response.response),
            )
        else:
            # Handle unknown content types
            raise ValueError(f"Unknown content type encountered: {part}")

    def from_history(self, history: History) -> List[types.Content]:
        """
        Convert common History format to Gemini-specific message format.

        Args:
            history: The common format history

        Returns:
            List of Gemini-specific messages
        """
        provider_history: List[types.Content] = []

        # Add context as a user message if it exists
        if history.context:
            provider_history.append(
                types.Content(
                    role="user", parts=[types.Part.from_text(text=history.context)]
                )
            )

        # Convert each message in the conversation
        for message in history.conversation:
            provider_history.append(
                types.Content(
                    role=message.role,
                    parts=[self._from_content_part(part) for part in message.content],
                )
            )

        return provider_history

    def to_history(self, provider_history: List[types.Content]) -> List[Message]:
        """
        Convert Gemini-specific history to common format messages.

        Args:
            provider_history: The Gemini-specific history

        Returns:
            List of common format messages
        """
        if not provider_history:
            return []

        common_messages = []
        start_index = 0

        # If we have a context message and should skip it
        if provider_history and provider_history[0].role == "user":
            start_index = 1

        # Convert each message
        for content in provider_history[start_index:]:
            common_content = [self._to_content_part(part) for part in content.parts]
            common_messages.append(Message(role=content.role, content=common_content))

        return common_messages

    def to_history_item(
        self,
        messages: List[GenerateContentPartWrapper] | List[ContentPartToolResult],
    ) -> Optional[types.Content]:
        """
        Convert chunks or tool results to a Gemini-specific message.

        Args:
            messages: The chunks or tool results to convert

        Returns:
            A Gemini-specific message, or None if no valid message can be created
        """
        if not messages:
            return None

        if isinstance(messages[0], ContentPartToolResult):
            return self._tool_results_to_message(messages)
        else:
            return self._content_blocks_to_message(messages)

    def _content_blocks_to_message(
        self, messages: List[GenerateContentPartWrapper]
    ) -> Optional[types.Content]:
        """
        Create a model message from content chunks.

        Args:
            chunks: The chunks to include in the message

        Returns:
            A model message with the content from all chunks
        """
        model_parts = []

        for chunk in messages:
            if chunk.get_text():
                model_parts.append(types.Part.from_text(text=chunk.get_text()))

            for tool_call in chunk.get_tool_calls():
                model_parts.append(
                    types.Part.from_function_call(
                        name=tool_call.name, args=tool_call.arguments
                    )
                )

        return types.Content(role="model", parts=model_parts)

    def _tool_results_to_message(
        self, messages: List[ContentPartToolResult]
    ) -> Optional[types.Content]:
        """
        Create a tool results message from tool results.

        Args:
            results: The tool results to include in the message

        Returns:
            A tool results message if there are results, None otherwise
        """
        if not messages:
            return None

        tool_parts = []
        for result in messages:
            tool_parts.append(
                types.Part.from_function_response(
                    name=result.name, response=result.content.model_dump()
                )
            )

        return types.Content(role="tool", parts=tool_parts)

    def create_chunk_wrapper(
        self,
        chunk: types.Part,
    ) -> ChunkWrapper[types.Part]:
        """
        Create a wrapper for provider-specific streaming content chunks.

        Args:
            chunk: The chunk to wrap

        Returns:
            A ChunkWrapper[T] implementation to access chunk data
        """
        return GenerateContentPartWrapper(chunk)
