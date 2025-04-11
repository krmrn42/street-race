import json
import logging
import os
import argparse
from llm.wrapper import ContentPartText, History
from tools.fs_tool import TOOLS, TOOL_IMPL
from messages import SYSTEM
from colors import AnsiColors
from llm.llmapi_factory import get_ai_provider
from llm.generate import generate_with_tools

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='generation.log')


def read_system_message():
    """
    Read the system message from a file or return the default message.

    Returns:
        str: The system message content
    """
    system_message_path = '.streetrace/system.md'
    if os.path.exists(system_message_path):
        try:
            with open(system_message_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading system message file: {e}")

    # Default system message
    return SYSTEM


def read_project_context():
    """
    Read all project context files from .streetrace directory excluding system.md.

    Returns:
        str: Combined content of all context files, or empty string if none exist
    """
    context_files_dir = '.streetrace'

    # Check if the directory exists
    if not os.path.exists(context_files_dir) or not os.path.isdir(context_files_dir):
        return ""

    # Get all files in the directory excluding system.md
    context_files = [
        os.path.join(context_files_dir, f) for f in os.listdir(context_files_dir)
        if os.path.isfile(os.path.join(context_files_dir, f)) and f != 'system.md'
    ]

    # If no context files found, return empty string
    if not context_files:
        return ""

    # Read and combine content from all context files
    context_content = []
    for file_path in context_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_name = os.path.basename(file_path)
                context_content.append(f"\n\n# Content from {file_name}\n\n{content}\n\n")
        except Exception as e:
            print(f"Error reading context file {file_path}: {e}")
            logging.error(f"Error reading context file {file_path}: {e}")

    return "".join(context_content)


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Run AI assistant with different models')
    parser.add_argument('--engine',
                        type=str,
                        choices=['claude', 'gemini', 'ollama', 'openai'],
                        help='Choose AI engine (claude, gemini, ollama, or openai)')
    parser.add_argument(
        '--model',
        type=str,
        help=
        'Specific model name to use (e.g., claude-3-7-sonnet-20250219, gemini-2.0-flash-001, llama3:8b, or gpt-4-turbo-2024-04-09)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help=
        'Prompt to send to the AI model (skips interactive mode if provided)')
    parser.add_argument(
        '--path',
        type=str,
        default=None,
        help=
        'Specify which path to use as the working directory for all file operations'
    )
    return parser.parse_args()


def call_tool(tool_name, args, original_call, work_dir):
    """
    Call the appropriate tool function based on the tool name.

    Args:
        tool_name: Name of the tool to call
        args: Dictionary of arguments to pass to the function
        original_call: The original function call object from the model
        work_dir: Path to use as the working directory for file operations

    Returns:
        tuple: (function_response, result_text)
    """
    print(AnsiColors.TOOL + f"{tool_name}: {args}" + AnsiColors.RESET)
    logging.info(f"Tool call: {tool_name} with {args}")
    if tool_name in TOOL_IMPL:
        tool = TOOL_IMPL[tool_name]
        if 'work_dir' in tool.__code__.co_varnames:
            args = { **args, 'work_dir': work_dir }
        try:
            result, view_result = tool(**args)
            print(AnsiColors.TOOL + str(view_result or result) + AnsiColors.RESET)
            logging.info(f"Function result: {result}")
            return {"success": True, "result": json.dumps(result)}
        except Exception as e:
            error_msg = f"Error in {tool_name}: {str(e)}"
            print(AnsiColors.TOOLERROR + error_msg + AnsiColors.RESET)
            logging.warning(error_msg)
            return {"error": str(e)}
    else:
        error_msg = f"Tool not found: {tool_name}"
        print(AnsiColors.TOOLERROR + error_msg + AnsiColors.RESET)
        logging.error(error_msg)
        return {'error': error_msg}



def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()

    # Set up the appropriate AI model
    model_name = args.model.strip().lower() if args.model else None
    provider_name = args.engine.strip().lower() if args.engine else None

    # Initialize conversation history
    conversation_history = History(
        system_message=read_system_message(),
        context=read_project_context())

    if conversation_history.context:
        print(AnsiColors.USER + "[Adding context]" + AnsiColors.RESET)

    # Get the working directory path
    working_dir = args.path if args.path else os.getcwd()
    if working_dir:
        print(f"Working in {working_dir}")

    def call_tool_f(tool_name, args, original_call):
        return call_tool(tool_name, args, original_call, working_dir)

    provider = get_ai_provider(provider_name)
    print(f"Using provider: {type(provider).__name__.replace('Provider', '')}")

    if args.prompt:
        conversation_history.add_message(role="user", content=[ContentPartText(args.prompt)])

        print(AnsiColors.USER + args.prompt + AnsiColors.RESET)
        logging.debug(f"User prompt: {args.prompt}")

        # Non-interactive mode with --prompt argument
        generate_with_tools(
            provider,
            model_name,
            conversation_history,
            TOOLS,
            call_tool_f,
        )
    else:
        # Interactive mode
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break

            conversation_history.add_message(role="user", content=[ContentPartText(user_input)])
            logging.debug(f"User prompt: {user_input}")

            generate_with_tools(
                provider,
                model_name,
                conversation_history,
                TOOLS,
                call_tool_f,
            )


if __name__ == "__main__":
    main()