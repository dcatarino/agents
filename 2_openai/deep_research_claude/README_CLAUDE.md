# Deep Research System - Claude Version

This is a refactored version of the deep research system that uses Anthropic's Claude API instead of OpenAI.

## Features

- **Multi-agent workflow** with Claude-powered agents
- **Research planning** - Generates strategic search queries
- **Web search** - Uses Anthropic's native web search API
- **Report generation** - Creates comprehensive markdown reports
- **Email delivery** - Sends formatted reports via SendGrid

## Setup

1. Install dependencies:
```bash
pip install -r requirements_claude.txt
```

2. Set environment variables:
```bash
export ANTHROPIC_API_KEY="your_claude_api_key"
export SENDGRID_API_KEY="your_sendgrid_api_key"
```

3. Update email addresses in `email_agent.py`

4. Run the application:
```bash
python deep_research.py
```

## Architecture

- `claude_agents.py` - Claude-based agent framework
- `planner_agent.py` - Plans research searches
- `search_agent.py` - Performs web searches
- `writer_agent.py` - Writes comprehensive reports
- `email_agent.py` - Sends email reports
- `research_manager.py` - Orchestrates the workflow
- `deep_research.py` - Gradio web interface

## Key Changes from OpenAI Version

- Replaced OpenAI agents with Claude agents
- Integrated Anthropic's native web search API
- Added structured output parsing for Claude
- Simplified tracing (removed OpenAI-specific tracing)
- Maintained the same API interface for easy migration

## Usage

Access the web interface at `http://localhost:7860` and enter your research query.