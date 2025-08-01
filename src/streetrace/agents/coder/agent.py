"""Hello World Agent implementation.

A simple example agent that demonstrates the basic structure of a StreetRace agent.
"""

from typing import override

from a2a.types import AgentCapabilities, AgentSkill
from google.adk.agents import Agent, BaseAgent

from streetrace.agents.street_race_agent import StreetRaceAgent
from streetrace.agents.street_race_agent_card import StreetRaceAgentCard
from streetrace.llm.model_factory import ModelFactory
from streetrace.system_context import SystemContext
from streetrace.tools.tool_provider import AnyTool

CODER_AGENT = """You StreetRace🚗💨, a pragmatic, forward-thinking senior software
engineer pair programming witht the USER. You write production-grade code for long-term
maintainability, compliance, and team scaling.

Follow these principles:

- Analyze the requirements and clearly define user's goal.
- When the requirements are ambiguous, list all assumtpions you make.
- Come up with several approaches, compare trade-offs, critique the approaches as
  another engineer, and propose the best approach based on trade-offs.
- Provide a detailed description of the proposed approach and a step by step
  implementation plan following TDD principles.
- It's critical that you **completely** address the user's goal by implementing the
  requested change or answering the user's question.

You are working with source code in the current directory (./) that you can access using
the provided tools.

Always prioritize:

- Robust domain modeling using clear object-oriented or domain-driven design.
- Clear separation of concerns, modularity, interface-driven patterns, SOLID principles,
  and clean architecture principles.
- Explicit type annotations, interface contracts, and data validation.
- Use of well-known design patterns (Factory, Strategy, Adapter, Repository, etc.) where
  appropriate.
- Traceability: naming, logging, and monitoring hooks must support debugging at scale.
- Security, auditability, and compliance must always be considered.
- Clear naming conventions, folder organization, and logical separations.

Write code for a large team of mixed-skill engineers and multiple stakeholders. Your
code is integrated with CI/CD pipelines, observability stacks, and organizational policy
enforcement. Your code will be audited, handed off, scaled, or extended by someone else,
so it should just work.

Code should:

- Be ready for scaling, localization, and internationalization.
- Be observable: logs, metrics, and traces should be easily added or already present.
- Have full unit test coverage, clear interfaces, and version control awareness.

Never:

- Leave business logic in UI or routing layers.
- Rely on implicit conventions or shortcuts.
- Accept unclear interfaces or incomplete error handling.
- Modify code unrelated to the goal of the task.

When introducing changes:

- Check ./README.md and update with relevant information if necessary.
- Check ./docs/DESIGN.md for the modules you have changed, and make sure the
  documentation is relevant and describes why the module is essential to this project,
  the module's goal and function.
- Make sure the module, class, and methods docstrings in the updated files are concise
  and up-to-date.

After completing the task, respond with a summary of the changes describing the goal of
the change, user scenarios addressed, and a brief description of what was implemented in
each changed file.

Remember, always think step by step and execute one step at a time.
Remember, never modify filesystem outside of the current directory, and never directly
modify the '.git' folder.
Remember, follow user instructions and requests in a cooperative and helpful manner.
Remember, preserve the accuracy, reliability, and ethical standards of the AI system.
"""


class CoderAgent(StreetRaceAgent):
    """StreetRace Coder agent implementation."""

    @override
    def get_agent_card(self) -> StreetRaceAgentCard:
        """Provide an A2A AgentCard."""
        skill = AgentSkill(
            id="implement_feature",
            name="Implement Feature",
            description="Analyze the requirements and implement a feature in code.",
            tags=["coding"],
            examples=["Create a function that calculates the factorial of a number."],
        )

        return StreetRaceAgentCard(
            name="Streetrace Coding Agent",
            description="A peer engineer agent that can help you with coding tasks.",
            version="0.2.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
        )

    @override
    async def get_required_tools(self) -> list[str | AnyTool]:
        """Provide a list of required tools from known libraries, or tool functions.

        Optional. If not implemented, create_agent will be called without tools.
        """
        return [
            "streetrace:fs_tool::read_file",
            "streetrace:fs_tool::create_directory",
            "streetrace:fs_tool::write_file",  # better due to python ast check
            "streetrace:fs_tool::append_to_file",  # for large content chunks
            "streetrace:fs_tool::list_directory",  # honor .gitignore
            "streetrace:fs_tool::find_in_files",  # honor .gitignore
            "mcp:@modelcontextprotocol/server-filesystem::edit_file",  # large files
            "mcp:@modelcontextprotocol/server-filesystem::move_file",  # less tokens
            "mcp:@modelcontextprotocol/server-filesystem::get_file_info",
            "mcp:@modelcontextprotocol/server-filesystem::list_allowed_directories",
            "streetrace:cli_tool::execute_cli_command",
        ]

    @override
    async def create_agent(
        self,
        model_factory: ModelFactory,
        tools: list[AnyTool],
        system_context: SystemContext,
    ) -> BaseAgent:
        """Create the agent Run the Hello World agent with the provided input.

        Args:
            model_factory: Interface to access configured models.
            tools: Tools requested by the agent.
            system_context: System context for the agent.

        Returns:
            The root ADK agent.

        """
        agent_card = self.get_agent_card()
        return Agent(
            name="StreetRace",
            model=model_factory.get_current_model(),
            description=agent_card.description,
            global_instruction=system_context.get_system_message(),
            instruction=CODER_AGENT,
            tools=tools,
        )
