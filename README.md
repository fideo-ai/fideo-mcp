# Fideo MCP Server

This repository exposes Fideo's Verify and Signals APIs through the [Model Context Protocol](https://modelcontextprotocol.io/) so that compatible AI assistants can inspect identity risk signals on demand. Both OpenAI's ChatGPT and Anthropic's Claude can call the tools once the server is configured locally.

## Features
- `get_verify`: high-level risk assessment with granular check results from [Fideo Verify](https://docs.fideo.ai/docs/verify).
- `get_signals`: rich profile intelligence from [Fideo Signals](https://docs.fideo.ai/docs/signals).

## Prerequisites
- Python 3.13+
- A Fideo API key with access to Verify and/or Signals (`FIDEO_API_KEY`)
- [`uv`](https://docs.astral.sh/uv/) or another way to install the Python dependencies listed in `pyproject.toml`
- (Optional) The [`mcp` CLI](https://github.com/modelcontextprotocol/python-sdk) for validating your setup

## Installation
```bash
# Clone the repository
git clone https://github.com/fideo-ai/fideo-mcp.git && cd fideo-mcp

# Install dependencies
uv sync  # or: pip install -e .
```

## Local Development
Set the API key and start the server. The script emits logs via the standard Python logging
configuration (stdout by default).

```bash
export FIDEO_API_KEY="REPLACE_ME"
uv run python fideo-mcp.py
```

When running in an MCP client the server will launch automatically, so you normally only need to 
configure the command and environment variable once.

## Configure with ChatGPT
ChatGPT Desktop (macOS/Windows) can connect to local MCP servers via JSON configuration files.

1. Ensure the Client side ChatGPT app is up to date
2. Create the config directory if it does not exist:
   ```bash
   mkdir -p "$HOME/.config/mcp"  # macOS & Linux
   ```
3. Save the following to `~/.config/mcp/fideo-mcp.json`:
   ```json
   {
     "name": "fideo-mcp",
     "command": ["uv", "run", "python", "fideo-mcp.py"],
     "env": {
       "FIDEO_API_KEY": "REPLACE_ME"
     }
   }
   ```
4. Restart ChatGPT and open *Settings → Capabilities → Model Context Protocol*.
5. Enable **fideo-mcp**. ChatGPT will launch the command above whenever it needs identity data.

## Configure with Anthropic Claude
Claude Desktop (macOS) and the Claude Web MCP integration use a similar JSON file convention.
Follow these [MCP Instructions](https://modelcontextprotocol.io/docs/develop/connect-local-servers) to stay current, but for local execution, this is what you'll need:
1. Update the Claude desktop app to the latest release with MCP support.
2. Create the configuration directory:
3. Save the following to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   "fideo-app": {
   "command": "~/.local/bin/uv",
   "args": [
     "--directory",
     "~/Documents/workspace/fideo-mcp",
     "run",
     "fideo-mcp.py"
     ]
   }   
   ```
4. Restart Claude. The server will appear under *Settings → Integrations → MCP*. Toggle it on to allow Claude to request Verify or Signals data.

> **Tip:** If you prefer `pip` instead of `uv`, replace the command with `"command": ["python", "fideo-mcp.py"]` and ensure your virtual environment is activated before launching the client.

## Tool Semantics
- Both tools return a JSON string prefixed with `---` to help chat clients stream raw data.
- Provide at least one identifier (email, phone, name + address, IP, or a social profile). Additional context improves match quality.
- Social profiles can be supplied either as individual fields (`social_network`, `social_id`, `social_handle`) or as a `profiles` list containing objects with `service`, `username`, `userid`, and/or `url` keys.
- Errors are surfaced as plain strings so the assistant can prompt you for missing or invalid inputs.

## Testing Without a Client
```bash
uv run python fideo-mcp.py  # runs the script, including a simple smoke test
```
Set `FIDEO_API_BASE` if you need to point at a non-production endpoint (e.g., a mock server).

## Contributing
Feel free to open issues or pull requests for fixes and new capabilities such as additional Fideo endpoints, caching layers, or richer response formatting.

## License
See [LICENSE](LICENSE) for details.
