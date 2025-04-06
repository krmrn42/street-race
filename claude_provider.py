"""
Claude AI Provider Implementation

This module implements the AIProvider interface for Anthropic's Claude models.
"""

import os
import logging
import anthropic  # pip install anthropic
import json
import time
from typing import List, Dict, Any, Callable, Optional, Union

from colors import AnsiColors
from ai_interface import AIProvider

# Constants
MAX_TOKENS = 200000  # Claude 3 Sonnet has a context window of approximately 200K tokens
MODEL_NAME = "claude-3-7-sonnet-20250219"


class ClaudeProvider(AIProvider):
    """
    Implementation of the AIProvider interface for Anthropic's Claude models.
    """
    
    def initialize_client(self) -> anthropic.Anthropic:
        """
        Initialize and return the Claude API client.
        
        Returns:
            anthropic.Anthropic: The initialized Claude client
            
        Raises:
            ValueError: If ANTHROPIC_API_KEY environment variable is not set
        """
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        return anthropic.Anthropic(api_key=api_key)

    def transform_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform tools from common format to Claude-specific format.
        
        Args:
            tools: List of tool definitions in common format
            
        Returns:
            List[Dict[str, Any]]: List of tool definitions in Claude format
        """
        claude_tools = [
            {
                "type": "custom",
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            } for tool in tools
        ]
        
        return claude_tools

    def pretty_print(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format message list for readable logging.
        
        Args:
            messages: List of message objects to format
            
        Returns:
            str: Formatted string representation
        """
        parts = []
        for i, message in enumerate(messages):
            content_str = str(message.get('content', 'NONE'))
            role = message.get('role', 'unknown')
            parts.append(f"Message {i + 1}:\n - {role}: {content_str}")
            
        return "\n".join(parts)

    def manage_conversation_history(self, conversation_history: List[Dict[str, Any]], max_tokens: int = MAX_TOKENS) -> bool:
        """
        Ensure conversation history is within token limits by intelligently pruning when needed.
        
        Args:
            conversation_history: List of message objects to manage
            max_tokens: Maximum token limit
            
        Returns:
            bool: True if successful, False if pruning failed
        """
        try:
            # Simplified token count estimation - would need actual token counting in production
            # This is a placeholder for an actual token counting function
            estimated_tokens = sum(len(str(msg)) for msg in conversation_history) // 4
            
            # If within limits, no action needed
            if estimated_tokens <= max_tokens:
                return True
                
            logging.info(f"Estimated token count {estimated_tokens} exceeds limit {max_tokens}, pruning...")
            
            # Keep first item (usually system message) and last N exchanges
            if len(conversation_history) > 3:
                # Keep important context - first message and recent exchanges
                preserve_count = min(5, len(conversation_history) // 2)
                conversation_history[:] = [conversation_history[0]] + conversation_history[-preserve_count:]
                
                # Recheck token count
                estimated_tokens = sum(len(str(msg)) for msg in conversation_history) // 4
                logging.info(f"After pruning: {estimated_tokens} tokens with {len(conversation_history)} items")
                
                return estimated_tokens <= max_tokens
            
            # If conversation is small but still exceeding, we have a problem
            logging.warning(f"Cannot reduce token count sufficiently: {estimated_tokens}")
            return False
            
        except Exception as e:
            logging.error(f"Error managing tokens: {e}")
            return False

    def generate_with_tool(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        call_tool: Callable,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        model_name: Optional[str] = MODEL_NAME,
        system_message: Optional[str] = None,
        project_context: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generates content using the Claude model with tools, maintaining conversation history.
        
        Args:
            prompt: The user's input prompt
            tools: List of tool definitions in common format
            call_tool: Function to call for tool execution
            conversation_history: The history of the conversation
            model_name: The name of the Claude model to use
            system_message: The system message to use
            project_context: Additional project context to be added to the user's prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List[Dict[str, Any]]: The updated conversation history
        """
        # Initialize client and conversation history
        client = self.initialize_client()
        if conversation_history is None:
            conversation_history = []

        model_name = model_name or MODEL_NAME

        # Use default system message if none is provided
        system_message = system_message or """You are an experienced software engineer implementing code for a project working as a peer engineer
with the user. Fullfill all your peer user's requests completely and following best practices and intentions.
If can't understand a task, ask for clarifications."""

        # Add context to the conversation history
        if project_context:
            print(AnsiColors.USER + "[Adding project context]" + AnsiColors.RESET)
            logging.debug(f"Context: {project_context}")
            conversation_history.append({
                'role': 'user',
                'content': [{
                    'type': 'text',
                    'text': project_context
                }]
            })

        # Add the user's prompt to the conversation history
        if prompt:
            print(AnsiColors.USER + prompt + AnsiColors.RESET)
            logging.info("User prompt: %s", prompt)
            conversation_history.append({
                'role': 'user',
                'content': [{
                    'type': 'text',
                    'text': prompt
                }]
            })

        messages = conversation_history.copy()

        # Ensure messages are within token limits
        if not self.manage_conversation_history(messages):
            print(AnsiColors.MODELERROR + "Conversation too large, cannot continue." + AnsiColors.RESET)
            return conversation_history

        continue_generation = True
        request_count = 0
        total_input_tokens = 0
        total_output_tokens = 0
        last_response = None

        while continue_generation:
            retry_count = 0
            while True:  # This loop handles retries for rate limit errors
                try:
                    request_count += 1
                    logging.info(
                        f"Starting chunk processing {request_count} with {len(messages)} message items using {model_name}."
                    )
                    logging.debug("Messages for generation:\n%s", self.pretty_print(messages))

                    # Create the message with Claude
                    last_response = client.messages.create(
                        model=model_name,
                        max_tokens=20000,
                        system=system_message,
                        messages=messages,
                        tools=self.transform_tools(tools))

                    logging.debug("Full API response: %s", last_response)
                    
                    if last_response.usage:
                        total_input_tokens += last_response.usage.input_tokens
                        total_output_tokens += last_response.usage.output_tokens
                    
                    # Break the retry loop if successful
                    break
                    
                except anthropic.RateLimitError as e:
                    retry_count += 1
                    wait_time = 30  # Wait for 30 seconds before retrying
                    
                    error_msg = f"Rate limit error encountered. Retrying in {wait_time} seconds... (Attempt {retry_count})"
                    logging.warning(error_msg)
                    print(AnsiColors.WARNING + error_msg + AnsiColors.RESET)
                    
                    time.sleep(wait_time)
                    continue
                    
                except Exception as e:
                    logging.exception(f"Error during API call: {e}")
                    print(AnsiColors.MODELERROR +
                          f"\nError during API call: {e}" +
                          AnsiColors.RESET)
                    # For non-rate limit errors, don't retry
                    raise

            model_messages = []
            tool_results = []

            for content_block in last_response.content:
                model_messages.append(content_block)
                if content_block.type == 'text':
                    print(AnsiColors.MODEL + content_block.text +
                        AnsiColors.RESET, end='')
                elif content_block.type == 'tool_use':
                    call_name = content_block.name
                    call_args = content_block.input
                    print(AnsiColors.TOOL + f"{call_name}: {call_args}" + AnsiColors.RESET)
                    logging.info(f"Tool call: {call_name} with {call_args}")

                    # Execute the tool
                    tool_result = call_tool(call_name, call_args, content_block)
                    
                    # Add tool result to outputs
                    tool_results.append({
                        'type': 'tool_result',
                        'tool_use_id': content_block.id,
                        'content': json.dumps(tool_result)
                    })
                    
            messages.append({
                'role': last_response.role,
                'content': model_messages})
            messages.append({
                'role': 'user',
                'content': tool_results})

            conversation_history[len(conversation_history):len(messages)] = messages[len(conversation_history):]

            # Continue only if there were tool calls
            continue_generation = last_response.stop_reason == 'tool_use'

        if last_response:
            print("\n" + AnsiColors.MODEL + f"Stop reason: {last_response.stop_reason}" +
                  AnsiColors.RESET)
            logging.info(f"Model has finished with reason: {last_response.stop_reason}")

        return conversation_history