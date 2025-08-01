# StreetRace🚗💨 Components Overview

## ./workflow/supervisor.py

Orchestrates the interaction loop between users and AI agents, forming the core workflow engine of StreetRace.

The Supervisor class manages the complete execution lifecycle of AI agent interactions:

1. **Session Management**: Creates and maintains ADK (Agent Development Kit) sessions, persisting conversation context between interactions using the JSONSessionService.

2. **Agent Creation**: Dynamically instantiates AI agents with appropriate tools and system context, configuring them for file operations and CLI command execution.

3. **Event Processing**: Handles events from Google ADK's Runner execution flow, rendering UI updates and capturing responses to maintain conversation continuity.

4. **Tool Integration**: Connects agents to system tools through ToolProvider, enabling file system operations, CLI command execution, and other capabilities required for coding assistance.

5. **History Management**: Maintains both session-specific state for ADK's context and global conversational history through HistoryManager for long-term memory across sessions.

The implementation follows a clear separation between:

- Session state (managed via ADK's Session objects) for tracking immediate interaction context
- Global history (managed via HistoryManager) for maintaining project-wide knowledge
- Tools (provided by ToolProvider) for enabling agent capabilities on the local system

Key architectural components and dependencies:

- `google.adk.Runner` for executing agent logic and handling event processing
- `google.adk.agents.Agent` for building the agent with appropriate configuration
- `google.adk.sessions` interfaces for managing conversation state
- `ToolProvider` for supplying file system and CLI capabilities
- `BaseSessionService` implementation for persisting sessions between interactions
- `LlmInterface` for interacting with language models through standardized interfaces
- `AgentManager` for discovering, validating, and creating agents
- `ModelFactory` for managing model creation and access

The Supervisor is instantiated in `app.py` with proper dependency injection of ModelFactory and AgentManager instances, following SOLID principles and enabling better testability. It serves as the core execution engine that processes each user prompt, manages agent responses, and handles the persistence of conversation state.

## ./agents/agent_manager.py

Manages the discovery, validation, creation, and lifecycle of specialized AI agents in the StreetRace ecosystem.

The AgentManager class provides a comprehensive agent management system:

1. **Agent Discovery**: Searches standard locations for agent implementations and validates their conformance to required interfaces.

2. **Interface Validation**: Ensures agents properly implement the StreetRaceAgent interface or provide legacy compatibility functions.

3. **Agent Creation**: Creates agent instances with necessary dependencies (models, tools) injected properly.

4. **Lifecycle Management**: Manages the async context for agent creation and cleanup through context managers.

5. **Backward Compatibility**: Supports both modern StreetRaceAgent implementations and legacy function-based agents.

The implementation follows clean architecture principles by:
- Providing a clear domain model through the StreetRaceAgent interface
- Implementing dependency injection for model and tool dependencies
- Using the async context manager pattern for resource lifecycle management
- Enforcing proper validation before allowing agent creation

This component is instantiated in the Supervisor and enables a modular agent ecosystem where specialized agents can be created for specific tasks while maintaining a consistent interface and lifecycle management.

## ./llm/model_factory.py

Provides a factory for creating and managing language model instances with efficient caching and configuration.

The ModelFactory class serves as a central point for model management:

1. **Model Configuration**: Manages model configurations and provides access to configured models.

2. **Interface Caching**: Creates and caches LlmInterface instances to avoid redundant initialization.

3. **Default Model Access**: Provides access to the default model based on configuration.

4. **Model Name Resolution**: Handles model name resolution and provides appropriate error handling.

The implementation follows the factory pattern to:
- Encapsulate the complexity of model creation and configuration
- Provide a clean interface for accessing models by name
- Enable efficient reuse of model instances
- Support dependency injection in agent creation

This component is used by the AgentManager and Supervisor to create and manage language model instances, providing a consistent interface for working with different model types and configurations.

## ./ui/ui_bus.py

Provides a decoupled event-driven communication system between UI and application logic through a publish-subscribe pattern.

The UiBus class acts as a central communication hub that decouples UI rendering from business logic:

1. **Event Distribution**: Implements a pub/sub pattern using Python's `pubsub` library, allowing components to subscribe to specific event types.

2. **UI Updates**: Provides a channel for any component to send renderable objects to the UI without direct coupling.

3. **Typing Feedback**: Enables real-time token counting and feedback during user input by dispatching typing events.

4. **Usage Tracking**: Facilitates the propagation of token usage and cost data from LLM interactions to UI components.

The implementation reduces coupling between components by allowing:

- Multiple subscribers for any event type
- Type-based event routing
- Asynchronous communication between components

This architecture makes the UI layer extensible and testable, as components communicate through standardized events rather than direct method calls.

## ./ui/console_ui.py

Provides the terminal-based user interface for StreetRace, handling all user input and formatted output display with robust error handling.

The ConsoleUI class manages the terminal interaction experience:

1. **Rich Text Rendering**: Uses the `rich` library to display formatted text with colors, styles, and structured layouts.

2. **Interactive Prompts**: Leverages `prompt_toolkit` to provide command history, autocompletion, and multiline input support.

3. **Status Feedback**: Implements a status spinner to provide visual feedback during LLM processing and other operations.

4. **Token Usage Display**: Shows real-time token usage and cost estimates in the UI toolbar.

5. **Keyboard Shortcuts**: Handles special key combinations for operations like multiline input (Esc+Enter) and cancellation (Ctrl+C).

6. **Error Recovery**: Implements graceful handling of MCP-related cancellation errors, returning special commands to signal retry scenarios.

The implementation carefully balances:

- Interactive responsiveness with asynchronous operations
- Rich visual feedback while maintaining clean terminal output
- Command completion with contextual suggestions based on file paths and commands
- Robust error handling that prevents application crashes from external service issues

The error handling specifically addresses MCP (Model Context Protocol) cancellation scope issues that can occur when background tasks are cancelled in different async contexts, implementing a graceful recovery mechanism that allows users to retry their operations.

This component integrates with UiBus to receive display requests from any part of the application, making it the single point of user interaction while remaining decoupled from business logic.

Dependencies include `prompt_toolkit` for interactive prompts and completion, and `rich` for formatted terminal output.

## ./ui/completer.py

Enhances user experience by providing intelligent auto-completion for file paths and commands in the command-line interface.

The completer module implements three key completion components:

1. **PathCompleter**: Suggests relevant file and directory paths when users type '@' mentions, enabling quick reference to project files without needing to type full paths.

2. **CommandCompleter**: Provides suggestions for available commands when users type '/' at the beginning of input, helping users discover and use the command interface efficiently.

3. **PromptCompleter**: Composes multiple completers into a unified interface, delegating completion requests to appropriate specialized completers based on input context.

The implementation carefully handles complex path completion scenarios by:
- Properly managing directory traversal and parent directory references
- Handling file path separators across different operating systems
- Filtering suggestions based on current input context for relevant results
- Providing visual differentiation between files and directories in completions

This component is instantiated in `app.py` and injected into the ConsoleUI, forming a critical part of the user experience by reducing cognitive load and typing effort. It directly improves productivity by making the file system and command interface more accessible through intelligent suggestions.

Dependencies include `prompt_toolkit` for the completion interface and integration with the console input system.

## ./commands/command_executor.py

Manages the registration and execution of all internal application commands through a centralized command registry.

The CommandExecutor class serves as the command dispatcher for the application:

1. **Command Registration**: Provides a registry for all Command instances, ensuring uniqueness and proper formatting.

2. **Command Discovery**: Identifies user inputs prefixed with '/' and routes them to the appropriate command handler.

3. **Execution Orchestration**: Handles the asynchronous execution of commands, including error management and status reporting.

4. **Command Metadata**: Exposes information about available commands for help documentation and auto-completion.

5. **Error Recovery Support**: Includes specialized commands like RetryCommand for handling connection issues and providing user feedback.

The implementation follows a command pattern design that:

- Decouples command handling from the main application flow
- Ensures command handlers are self-contained with clear responsibilities
- Provides a consistent interface for error handling and execution status
- Supports error recovery scenarios through specialized command handlers

This component is instantiated early in the application lifecycle within `app.py` and forms the foundation for the command-line interface. It integrates with the ConsoleUI through the CommandCompleter for command auto-completion and with Application to process user commands before they are sent to the AI agent.

The design allows new commands to be easily added by registering additional Command implementations, supporting extensibility without modifying the core execution logic. This includes commands for error recovery scenarios, such as the RetryCommand that handles MCP connection issues gracefully.

## ./llm/llm_interface.py

Provides a standardized interface to various language model providers while abstracting implementation details from the rest of the application.

The LlmInterface module serves as a key abstraction layer for AI model interactions:

1. **Abstraction Layer**: Defines a common interface through the LlmInterface abstract base class for working with different LLM providers.

2. **Factory Pattern**: Implements the get_llm_interface factory function to create appropriate LLM interface instances based on model configuration.

3. **Token Estimation**: Provides token counting functionality to estimate prompt size before sending to the LLM.

4. **API Standardization**: Normalizes the interaction with different AI models through a consistent generate_async method that accepts standardized message and tool formats.

The implementation uses dependency inversion to ensure:
- Core application logic can use any LLM provider without modification
- New LLM providers can be added by implementing the LlmInterface abstract class
- Testing can use mock implementations of LlmInterface for predictable behavior

This component is instantiated in `app.py` and injected into the Supervisor, forming a critical link in the application's ability to interact with AI models while maintaining loose coupling with specific provider implementations.

## ./llm/lite_llm_client.py

Implements resilient LLM client functionality with retry logic, usage tracking, and cost calculation capabilities.

The LiteLLMClientWithUsage and RetryingLiteLlm classes extend Google ADK's LLM implementation:

1. **Retry Mechanism**: Implements robust error handling with exponential backoff for rate limits and server errors through the RetryingLiteLlm class.

2. **Cost Tracking**: Captures token usage statistics and calculates costs using litellm's cost calculator, publishing this data through the UiBus.

3. **Error Handling**: Provides detailed error reporting for various failure modes, ensuring issues are properly logged and communicated to users.

4. **Performance Optimization**: Balances between stream and non-stream modes for optimal performance based on the use case.

The implementation carefully handles the complexities of:
- LLM API failures and transient errors
- Detailed token usage tracking for cost management
- Graceful degradation during service disruptions

These components form the foundation of StreetRace's reliable AI interaction capabilities, ensuring consistent behavior even when third-party services experience issues.

Dependencies include Google's ADK framework for the base LLM interface and litellm for standardized access to multiple LLM providers.

## ./tools/tool_provider.py

Centralizes tool discovery and provisioning for AI agents, including MCP (Model Context Protocol) integration and error handling.

The ToolProvider class manages the entire tool ecosystem:

1. **Tool Provisioning**: Collects and provides tools from multiple sources - static tools, StreetRace modules, and MCP servers.

2. **MCP Integration**: Creates and manages MCPToolset instances for external tool servers, with robust error handling for connection issues.

3. **Error Resilience**: Implements graceful degradation when MCP servers fail to connect, allowing the application to continue with available tools.

4. **Tool Resolution**: Parses tool references and resolves them to actual implementations, supporting multiple naming schemes and sources.

5. **Context Management**: Ensures tools receive necessary context (like working directory) while hiding implementation details from agents.

The implementation includes comprehensive error handling for MCP-related issues:
- Catches and logs MCP toolset creation failures
- Continues operation with partial tool availability when some servers are unreachable
- Provides detailed logging for debugging connection issues

This component is critical for enabling agents to access external capabilities through the MCP protocol while maintaining system stability when external services are unavailable.

## ./tools/fs_tool.py

Provides standardized file system operations for AI agents, enabling safe file manipulation within the working directory.

The fs_tool module implements core file system tools that allow agents to:

1. **File Reading/Writing**: Safely read and write files with proper error handling and path validation.

2. **Directory Management**: Create and list directories with respect to .gitignore rules.

3. **Content Searching**: Find specific text patterns within files across the project.

4. **Path Sanitization**: Clean and validate paths to prevent directory traversal or access outside the working directory.

The implementation enforces strict security boundaries by:
- Containing all operations within the specified working directory
- Validating file paths to prevent directory traversal attacks
- Providing standardized error responses for failed operations

These tools are essential for enabling AI agents to understand and manipulate the local file system in a controlled manner, making them core to the project's ability to assist with coding tasks.

The fs_tool module is wrapped by the ToolProvider in `app.py` and made available to AI agents through the Google ADK tool interface.

## ./tools/cli_tool.py

Enables AI agents to execute CLI commands in a controlled, sandboxed environment while capturing command output.

The cli_tool module provides a simplified interface for executing command-line operations:

1. **Command Execution**: Runs CLI commands in a subprocess with proper output capturing.

2. **Output Streaming**: Collects stdout and stderr output from commands for analysis by the AI agent.

3. **Working Directory Control**: Ensures commands execute within the specified project directory.

This tool delegates to the underlying implementation in the definitions directory, maintaining a clean interface for tool consumption while the safety checks are handled by the cli_safety module.

## ./tools/agent_tools.py

Provides specialized tools for agent discovery and management that enable the primary AI assistant to find and utilize other agents in the system.

The agent_tools module implements agent management functionality:

1. **Agent Discovery**: Searches predefined locations for valid agent implementations with the `list_agents` function.

2. **Tool Discovery**: Provides information about available tools that can be given to agents with the `list_tools` function.

3. **Metadata Extraction**: Extracts agent metadata from get_agent_metadata() functions in agent modules, with fallback to README files.

4. **Configuration-Based Tools**: Loads tool definitions from YAML configuration files for a flexible, maintainable tool registry.

5. **Agent Execution**: Enables running specialized agents through the `run_agent` function, allowing the primary agent to delegate tasks.

The implementation supports a modular agent ecosystem by:
- Standardizing how agents are discovered and described
- Providing a clear API for tool discovery and capabilities
- Maintaining clean separation between agent discovery and execution
- Using configuration files for tool definition to enable easy updates
- Supporting both modern StreetRaceAgent implementations and legacy function-based agents

These tools enable a hierarchical agent architecture where the primary AI assistant can discover, select, and invoke specialized agents for specific tasks, supporting a more modular and extensible system.

## ./tools/cli_safety.py

Implements a robust security layer for analyzing and classifying CLI command safety before execution.

The cli_safety module provides critical security functionality:

1. **Command Analysis**: Uses bashlex to parse and analyze command structure for safety evaluation.

2. **Safety Classification**: Categorizes commands into safe, ambiguous, or risky based on command name and arguments.

3. **Path Validation**: Identifies and prevents execution of commands with absolute paths or directory traversal attempts.

4. **Allowlist Enforcement**: Maintains a list of known-safe commands while requiring additional scrutiny for others.

The implementation balances security with functionality by:
- Allowing common development tools (git, python, npm, etc.) by default
- Preventing commands that could affect system state outside the project directory
- Providing detailed logging of command safety decisions for auditing

This security layer is crucial for enabling AI agents to execute commands without compromising system security, making it a key component of the project's sandboxing strategy.

The module integrates with cli_tool.py to ensure all commands are analyzed before execution, following the "fail-fast" approach for security-critical components.

## ./utils/hide_args.py

Provides a decorator for function signature manipulation to selectively hide and auto-inject arguments.

The hide_args module offers a powerful decorator that:

1. **Signature Manipulation**: Modifies function signatures to hide specific parameters, making them invisible to external callers.

2. **Docstring Adaptation**: Automatically updates function docstrings to remove references to hidden parameters.

3. **Automatic Injection**: Injects specified values for hidden parameters at runtime without the caller needing to provide them.

4. **Type Safety**: Preserves the original function's return type annotations for type checking compatibility.

This utility is critical for the tool architecture in StreetRace, allowing tools to receive contextual information (like working directory) automatically without exposing these implementation details to the AI agent. It enables a clean interface while maintaining internal consistency.

The implementation is used extensively in the ToolProvider to hide the working directory parameter from tool functions, ensuring tools always operate within the specified project directory without requiring the agent to specify this parameter explicitly.

## ./utils/uid.py

Provides reliable user identification through multiple fallback methods to support session management.

The uid module implements a robust user identity resolution system that:

1. **GitHub Integration**: Attempts to retrieve the user's GitHub login via the GitHub CLI when available.

2. **Git Configuration**: Falls back to the user's Git configuration to determine identity.

3. **OS Identity**: Uses the operating system username as a final fallback method.

This utility ensures that StreetRace can reliably identify users across different environments for session tracking and attribution, supporting the project's goal of maintaining coherent conversation history.

The module is used in the Args class to determine the effective user ID for session management, providing a consistent way to identify sessions across different invocations of the application.
---
### scripts/compare_profiles.py

**Goal & Function**: Compares the output JSONs of `scripts/profile_startup.py` from two different commits (typically, main branch vs. PR branch) and emits a Markdown report with key deltas for performance metrics. Intended for CI usage to visualize startup performance regressions and improvements directly in PR comments.

**Why Essential**: Automates the detection and report of user-facing startup performance regressions. Ensures every PR is transparently evaluated for speed impact, promoting a fast and responsive developer experience.
