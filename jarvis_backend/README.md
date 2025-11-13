# Jarvis - AI Assistant

A fully functional Python-based CLI AI assistant powered by Google Gemini, with persistent memory, web search, system command execution, and a modular skill system.

## Features

- 🤖 **AI Brain**: Powered by Google Gemini for natural language understanding
- 🧠 **Persistent Memory**: PostgreSQL for structured data + ChromaDB for semantic search
- 🔍 **Web Search**: DuckDuckGo integration for real-time information
- ⚡ **System Integration**: Open apps and execute system commands
- 🔌 **Modular Skills**: Easy-to-extend plugin system
- 🎯 **Intent Recognition**: Automatic intent extraction and task planning
- 👤 **Personalization**: Remembers user preferences and adapts behavior
- 📝 **Conversation History**: Full conversation tracking with semantic search

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Google Gemini API key
- Serper.dev API key (for web search - get free key from https://serper.dev/)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd jarvis_backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database:**

   **Option 1: Using Docker (Recommended):**
   ```bash
   # Run PostgreSQL in Docker
   docker run --name jarvis-postgres \
     -e POSTGRES_USER=jarvis \
     -e POSTGRES_PASSWORD=jarvis \
     -e POSTGRES_DB=jarvis_db \
     -p 5432:5432 \
     -d postgres:15
   
   # Or using docker-compose (create docker-compose.yml):
   # version: '3.8'
   # services:
   #   postgres:
   #     image: postgres:15
   #     container_name: jarvis-postgres
   #     environment:
   #       POSTGRES_USER: jarvis
   #       POSTGRES_PASSWORD: jarvis
   #       POSTGRES_DB: jarvis_db
   #     ports:
   #       - "5432:5432"
   #     volumes:
   #       - postgres_data:/var/lib/postgresql/data
   # volumes:
   #   postgres_data:
   # 
   # Then run: docker-compose up -d
   ```

   **Option 2: Local PostgreSQL installation:**
   ```bash
   # Create database
   createdb jarvis_db
   
   # Or using psql:
   psql -U postgres -c "CREATE DATABASE jarvis_db;"
   ```

4. **Configure environment variables:**
   ```bash
   cp config/.env.example config/.env
   ```
   
   Edit `config/.env` and add your credentials:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   DATABASE_URL=postgresql://jarvis:jarvis@localhost:5433/jarvis_db
   ```
   
   **Note:** 
   - If using Docker, the DATABASE_URL should match the Docker container credentials (user: jarvis, password: jarvis).
   - Get a free Serper.dev API key from https://serper.dev/ (2500 free searches/month). If not provided, the system will fallback to DuckDuckGo (may have rate limits).

5. **Initialize the database:**
   The database tables will be created automatically on first run.

## Usage

### Running as FastAPI Server (Recommended for Frontend)

**Start the server:**
```bash
python server.py
# Or with uvicorn directly:
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**API Endpoints:**
- `POST /ask` - Ask a question or give a command
- `GET /memory/show` - View memory contents
- `POST /memory/search` - Search semantic memory
- `POST /memory/clear` - Clear conversation history
- `GET /skills` - List all available skills
- `GET /conversation/history` - Get conversation history
- `WebSocket /ws` - Real-time chat via WebSocket

**Example API Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "verbose": false}'
```

### Example API Interactions

**Simple question:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

**Open an application:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "open vscode"}'
```

**Web search:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "search latest python 3.12 features"}'
```

**Multi-step task:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "open chrome and search for AI news"}'
```

**View memory:**
```bash
curl -X GET "http://localhost:8000/memory/show"
```

**Search memory:**
```bash
curl -X POST "http://localhost:8000/memory/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "python", "limit": 5}'
```

## Architecture

### Core Modules

- **`brain.py`**: Gemini LLM interface and conversation management
- **`intent.py`**: Intent extraction from user messages
- **`planner.py`**: Task decomposition and step planning
- **`memory.py`**: PostgreSQL + ChromaDB memory management
- **`search.py`**: DuckDuckGo web search wrapper
- **`executor.py`**: System command and app execution
- **`personalization.py`**: User preference management
- **`skill_registry.py`**: Dynamic skill loading system

### Skills System

Skills are Python files in the `skills/` directory. Each skill:
- Inherits from `Skill` base class
- Implements a `run(parameters)` method
- Has `name` and `description` attributes

Example skill:
```python
from core.skill_registry import Skill
from typing import Dict, Any

class MySkill(Skill):
    name = "my_skill"
    description = "Does something useful"
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Your logic here
        return {"success": True, "result": "..."}
```

### Memory System

**Structured Memory (PostgreSQL):**
- User preferences (key-value pairs)
- Conversation history
- User facts

**Semantic Memory (ChromaDB):**
- Embedded conversation history
- Similarity-based retrieval
- Context-aware responses

## Configuration

Edit `config/settings.py` or set environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_MODEL`: Model to use (default: "gemini-1.5-flash")
- `TEMPERATURE`: LLM temperature (default: 0.7)
- `MAX_CONVERSATION_HISTORY`: Max conversation turns in memory (default: 50)

## Project Structure

```
jarvis_cli/
├── server.py              # FastAPI server entry point
├── jarvis.md              # Jarvis identity and purpose document
├── requirements.txt        # Dependencies
├── README.md              # This file
├── config/
│   ├── settings.py        # Configuration
│   └── .env.example       # Environment template
├── core/
│   ├── brain.py           # LLM interface
│   ├── intent.py          # Intent extraction
│   ├── planner.py         # Task planning
│   ├── memory.py          # Memory management
│   ├── search.py          # Web search
│   ├── executor.py        # System execution
│   ├── personalization.py # User preferences
│   └── skill_registry.py  # Skill loader
├── routes/
│   ├── ask.py             # Ask endpoint routes
│   ├── memory.py          # Memory management routes
│   ├── skills.py          # Skills listing routes
│   ├── conversation.py     # Conversation history routes
│   └── websocket.py       # WebSocket routes
├── schemas/
│   ├── ask.py             # Ask request/response schemas
│   ├── memory.py          # Memory schemas
│   └── general.py        # General schemas
├── skills/
│   ├── open_app.py        # Open applications
│   ├── web_search.py      # Web search skill
│   ├── run_command.py     # Command execution
│   ├── read_file.py       # File reading
│   └── conversational.py  # General chat
└── data/
    └── chroma_db/         # ChromaDB storage (auto-created)
```

## Development

### Adding New Skills

1. Create a new Python file in `skills/`
2. Inherit from `Skill` class
3. Implement `run()` method
4. The skill will be automatically loaded on next run

### Extending Memory

The memory system automatically saves:
- User preferences (extracted from conversation)
- Facts about the user
- Conversation history
- Semantic embeddings

To manually save data:
```python
from core.memory import memory_manager

memory_manager.save_preference("key", "value")
memory_manager.save_fact("fact_key", "fact_value")
```

## Troubleshooting

**Database connection errors:**
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database exists

**Gemini API errors:**
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits

**Skill loading errors:**
- Check skill files are valid Python
- Ensure skills inherit from `Skill` class
- Check for syntax errors in skill files

## License

MIT License - feel free to use and modify as needed.

## Contributing

This is a personal project, but suggestions and improvements are welcome!

