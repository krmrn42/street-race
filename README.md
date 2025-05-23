# StreetRace🚗💨

Today, StreetRace🚗💨 is a CLI-based assistant that can run agentic workflows, maintain
your conversation histories, allowing full customization, and using any model supported
by [BerriAI/litellm](https://github.com/BerriAI/litellm), including self-hosted ollama
models.

The goal is to enable:

1. Creating and using agents in your day-to-day SWE/SRE workflows.
2. Publishing and running your agents and other code to cloud envs.
3. Debugging, code generation, and diagnostics from CLI.

Here is a workflow that describes what StreetRace🚗💨 aims to be in v.1:

```bash
> streetrace
You: Create an agent that takes issues from our tracker API (documented in
..... @apis/my_issue_tracker.yaml), takes the latest issue with the highest priority,
..... and implements it. When complete and the implementation fully satisfies the
..... described requirements, publishes a PR on GitHub.
StreetRace: Working...
StreetRace: Your agent is created as "IssueFixer".
You: Deploy @IssueFixer and run it in a loop.
StreetRace: Working...
StreetRace: Deploying IssueFixer to yourk8shost.foo.bar...
StreetRace: IssueFixer is started and available at A2A endpoint issuefixer-001.foo.bar.
IssueFixer: There are 39 unresolved issues. Taking issue ISS007.
IssueFixer: Based on the issue description, I need to fix the app so it works.
IssueFixer: Looking for a solution...
IssueFixer: ...
IssueFixer: ISS007 is fixed, taking ISS042 now...
...
```

## Installation and usage

### Install from pip

```bash
$ pip install streetrace
```

### Install from source

The code is managed by `poetry`. If it's not already installed, follow the [poetry
install guide](https://python-poetry.org/docs/#installation).

```bash
$ git clone git@github.com:krmrn42/street-race.git
$ cd street-race --model=$YOUR_FAVORITE_MODEL
$ poetry install
```

Where `$YOUR_FAVORITE_MODEL` is the
[LiteLLM provider route](https://docs.litellm.ai/docs/providers) (`provider/model`).

### Environment Setup

Follow relevant LiteLLM guides to set up environment for a specific model. For example,
for commercial providers, set your regular API key in the environment
(`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, etc), or `OLLAMA_API_URL` for
local Ollama models.

### Usage

`streetrace` is a CLI, and it can be installed as your dev dependency, pipx, or your
preferred way. You don't need it as a regular dependency in your project.

```bash
$ streetrace
You: Type your prompt
```

### Command Line Arguments

#### Session Management

StreetRace🚗💨 supports persistence of conversations through sessions. You can specify:

- `--app-name` - Application name for the session (defaults to the current working
  directory name)
- `--user-id` - User ID for the session (defaults to your GitHub username, Git username,
  or OS username)
- `--session-id` - Session ID to use or create (defaults to current timestamp)
- `--list-sessions` - List all available sessions for the current app and user

Examples:

```bash
# List all sessions for the current app and user
$ streetrace --list-sessions

# Create or continue a specific session
$ streetrace --session-id my-project-refactoring

# Work with a specific app name and user
$ streetrace --app-name my-project --user-id john.doe --session-id feature-x
```

If no session arguments are provided, StreetRace🚗💨 will:

1. Use the current working directory name as the app name
2. Use your detected user identity as the user ID
3. Create a new session with a timestamp-based ID

This allows you to maintain separate conversation contexts for different projects or
tasks.

If you want to work with the same agent/context across multiple runs, use the same
session ID.

#### Working with Files in Another Directory

The `--path` argument allows you to specify a different working directory for all file
operations:

```bash
$ streetrace --path /path/to/your/project
```

This path will be used as the working directory (work_dir) for all tools that interact
with the file system, including:

- `list_directory`
- `read_file`
- `write_file`
- `find_in_files`
- as a cwd in cli commands.

This feature makes it easier to work with files in another location without changing
your current directory.

### Interactive Mode

When run without `--prompt`, StreetRace🚗💨 enters interactive mode.

#### Autocompletion

- Type `@` followed by characters to autocomplete file or directory paths relative to
  the working directory.
- Type `/` at the beginning of the line to autocomplete available internal commands.

#### Internal Commands

These commands can be typed directly into the prompt (with autocompletion support):

- `/help`: Display a list of all available commands with their descriptions.
- `/exit`: Exit the interactive session.
- `/quit`: Quit the interactive session.
- `/history`: Display the conversation history.
- `/compact`: Summarize conversation history to reduce token count.
- `/reset`: Reset the current session, clearing the conversation history.

For detailed information about the `/compact` command, see
[docs/commands/compact.md](docs/commands/compact.md).

### Non-interactive Mode

You can use the `--prompt` argument to run StreetRace🚗💨 in non-interactive mode:

```bash
$ streetrace --prompt "List all Python files in the current directory"
```

This will execute the prompt once and exit, which is useful for scripting or one-off
commands.

### CLI Command Safety

StreetRace🚗💨 includes an experimental safety mechanism for CLI command execution.
Each command requested by the AI is analyzed and categorized into one of three safety
levels:

- **Safe**: Commands from a pre-configured safe list with only relative paths
- **Ambiguous**: Commands not in the safe list but without obvious risks
- **Risky**: Commands with absolute paths, directory traversal attempts, or potentially
  dangerous operations

Risky commands are blocked by default to prevent unintended filesystem operations or
system changes. This adds a layer of protection when working with AI-suggested commands.

The safety checker uses `bashlex` to parse and analyze commands and arguments, checking
for:

- Command presence in a predefined safe list
- Use of absolute vs. relative paths
- Directory traversal attempts (using `..` to move outside the working directory)

This helps ensure that StreetRace🚗💨 operates within the intended working directory and
with known-safe commands.
