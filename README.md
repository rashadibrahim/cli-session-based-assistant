# Session-based personal AI assistant with voice & text CLI

A session-based AI assistant with a FastAPI backend, a CLI interface (text + voice), and a dedicated SQL notes agent. It supports multi-session chat, optional history, automatic summarization, and tool access for notes, email, time, and web search.

## Key Features

- **Session-based conversations**: Create multiple sessions, each with its own name and chat history.
- **History + summarization**: Enable history per request; older context is summarized and stored to keep conversations compact.
- **Notes SQL agent**: Natural-language control of a notes database (add, update, search, list, archive, tags).
- **CLI user interface**: Menu-driven client with **text mode** and **voice mode** (record voice, get voice reply).
- **Tooling**: Time lookup, web search, email sending, and database access.

## Architecture Overview

- **API**: FastAPI server in [api.py](api.py) exposes session and chat endpoints.
- **Main agent**: [agents/main_agent.py](agents/main_agent.py) routes requests to tools.
- **SQL notes agent**: [agents/sql_agent.py](agents/sql_agent.py) with LangChain SQL toolkit.
- **Summarization**: [agents/summarization_agent.py](agents/summarization_agent.py) summarizes long chat history.
- **Databases**:
  - Notes DB: [databases/notes_database.py](databases/notes_database.py)
  - Sessions DB: [databases/session_database.py](databases/session_database.py)
- **CLI**: [cli.py](cli.py) for text + voice chat and session management.

## Notes SQL Agent (Notes Database)

The SQL agent is designed specifically for the **notes database** so it can handle:

- **Adding notes**
- **Updating notes**
- **Searching notes** (by title/content/tags)
- **Listing notes** (recent, archived, tagged, etc.)
- **Archiving or deleting notes**

### Notes Database Schema
- **notes**: `id`, `title`, `content`, `created_at`, `updated_at`, `is_archived`
- **tags**: `id`, `name`
- **note_tag**: many-to-many association between notes and tags

### How the SQL Agent is used
The main agent exposes a tool named **`database_agent`**. When a user asks anything related to notes (create, update, search, list, archive), the main agent routes the request to the SQL agent, which generates SQL against the notes database and returns results.

**Example prompts**:
- “Add a note titled ‘Meeting’ with content ‘Discuss Q1 goals’ and tag it ‘work’.”
- “List my latest 5 notes.”
- “Search notes mentioning ‘budget’.”
- “Archive the note titled ‘Old plan’.”

## Summarization

The system automatically summarizes long chat histories. When a session becomes large, a summary is created and stored as a special message. This keeps context small while preserving key decisions and open items.

## Sessions & History

This is a **session-based agent**:
- Create multiple sessions, each with a name.
- Each session stores its own chat history.
- You can enable or disable history per request (`enable_history`).
- Summaries are created automatically when needed.

## API Endpoints

- **POST** `/sessions/create` — create a new session (optional name)
- **GET** `/sessions` — list sessions
- **GET** `/sessions/{session_id}` — get session details + history
- **DELETE** `/sessions/{session_id}` — delete a session
- **POST** `/query/chat` — send a message to the agent

Example request body for chat:
```json
{
  "query": "List my latest notes",
  "session_id": "<session-id>",
  "enable_history": true
}
```

## CLI (Text + Voice)

The CLI provides full access to sessions and chat:

- **Text mode**: type messages and receive text responses.
- **Voice mode**: record audio → transcribe with Deepgram → agent reply → audio playback.

The CLI includes a menu to create, list, select, and delete sessions.

## Environment Variables

1- Create a `.env` file in the project root with the keys you use:

```
# LLM & Text-to-Speech
GROQ_API_KEY=...

# Speech-to-text
DEEPGRAM_API_KEY=...

```

2- Create a `.env` file in the agents folder with the keys you use:

```
# LLM (SQL Agent)
GROQ_API_KEY=...

# Email tool
MAIL_ACCOUNT=...
MAIL_PASSWORD=...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Web search tool
TAVILY_API_KEY=...

```

3- Create a `.env` file in the databases folder with the keys you use:

```
# Databases (optional overrides)
NOTES_DATABASE_URL=sqlite:///./notes.db
SESSION_DATABASE_URL=sqlite:///./agent_sessions.db
```

## Installation

1. Create and activate a virtual environment
2. Install dependencies
3. Run the API
4. Start the CLI

> Note: dependency versions depend on your environment. Typical packages include:
> `fastapi`, `uvicorn`, `langchain`, `langchain-groq`, `langchain-community`, `sqlalchemy`, `python-dotenv`, `requests`, `pyaudio`, `deepgram-sdk`, `pygame`.

## Run the API

```bash
python api.py
```

## Run the CLI

```bash
python cli.py
```

## Publishing Notes

- This project is designed to be published as a full-stack assistant with a CLI front-end.
- The SQL agent is scoped to the notes database and can handle end-to-end note management.
- Summarization is automatic and session-aware.

---

If you want a shorter README or a “quickstart only” version, tell me and I’ll trim it.
