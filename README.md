# Web Operator Agent

A sophisticated web automation agent inspired by OpenAI's Operator, built with **LangGraph 0.4.8** for agent orchestration and **FastAPI** for the API layer. This implementation provides autonomous web browsing capabilities with intelligent decision-making, safety checks, and visual analysis.

## 🚀 Features

- **🧠 Intelligent Web Automation**: Uses GPT-4o to understand and execute complex web tasks
- **🌐 Full Browser Control**: Powered by Playwright for comprehensive web interaction
- **🛡️ Safety First**: Multi-layer confirmation system and domain filtering
- **👁️ Computer Vision**: OpenCV-based element detection and visual analysis
- **🔄 Multi-step Workflows**: Complex task execution orchestrated by LangGraph
- **📊 Real-time Monitoring**: Live task status tracking and screenshot capture
- **🚀 RESTful API**: Complete FastAPI backend with interactive documentation
- **🐳 Production Ready**: Docker support with Redis state management

## 🏗️ Architecture

The system follows a modular architecture with clear separation of concerns:

```
├── core/           # Core configuration, models, and logging
│   ├── config.py   # Environment-based configuration
│   ├── models.py   # Pydantic data models
│   └── logging.py  # Structured logging setup
├── tools/          # Specialized automation tools
│   ├── browser.py  # Playwright browser automation
│   ├── vision.py   # OpenCV computer vision
│   └── llm.py      # GPT-4o integration
├── nodes/          # LangGraph workflow nodes
│   ├── planning.py # Task analysis and planning
│   ├── execution.py # Action execution
│   └── control.py  # Flow control and decisions
├── api/            # FastAPI REST API
│   └── main.py     # API endpoints and handlers
├── workflow.py     # LangGraph state machine
└── main.py         # Application entry point
```

## 📦 Quick Start

### 1. Installation

```bash
git clone <your-repo>
cd operator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

### 2. Configuration

```bash
cp .env.example .env
# Edit .env with your OpenAI API key:
# OPENAI_API_KEY=your_api_key_here
```

### 3. Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8001` with interactive API docs at `/docs`.

### 4. Quick Test

```bash
# Run the demo
python demo.py

# Or use the interactive client
python client.py interactive
```

## 🎯 Usage Examples

### Example 1: Simple Navigation

```python
import asyncio
from client import WebOperatorClient

async def main():
    client = WebOperatorClient()

    # Create a navigation task
    task = await client.create_task(
        description="Go to https://httpbin.org and take a screenshot",
        url="https://httpbin.org"
    )

    # Wait for completion
    result = await client.wait_for_completion(task["task_id"])
    print(f"Result: {result['status']}")

asyncio.run(main())
```

### Example 2: Form Automation

```python
task = await client.create_task(
    description="Fill out the contact form with test data and submit",
    url="https://example.com/contact"
)
```

### Example 3: Search and Extract

```python
task = await client.create_task(
    description="Search for 'LangGraph tutorials' and extract the top 3 results",
    url="https://duckduckgo.com"
)
```

## 🌐 API Endpoints

| Method | Endpoint                   | Description                   |
| ------ | -------------------------- | ----------------------------- |
| `GET`  | `/health`                  | System health check           |
| `POST` | `/tasks/`                  | Create new automation task    |
| `GET`  | `/tasks/`                  | List all tasks                |
| `GET`  | `/tasks/{task_id}`         | Get task status               |
| `POST` | `/tasks/{task_id}/confirm` | Confirm pending action        |
| `GET`  | `/screenshots/{filename}`  | Download screenshot           |
| `GET`  | `/docs`                    | Interactive API documentation |

### Task Creation

```bash
curl -X POST "http://localhost:8001/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Navigate to Google and search for OpenAI",
    "url": "https://google.com",
    "priority": "medium"
  }'
```

### Task Monitoring

```bash
curl "http://localhost:8001/tasks/{task_id}"
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o

# Browser Configuration
BROWSER_TYPE=chromium
HEADLESS=false
BROWSER_TIMEOUT=30000

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=true

# Safety & Monitoring
MAX_EXECUTION_TIME=300
ENABLE_SCREENSHOTS=true
SCREENSHOT_PATH=./screenshots
```

Edit `.env` with your settings:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Browser Configuration
BROWSER_TYPE=chromium
HEADLESS=false
BROWSER_TIMEOUT=30000

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🚀 Quick Start

1. **Start the server**:

```bash
python main.py
```

2. **Open API documentation**: http://localhost:8000/docs

3. **Create a task**:

```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Go to Google and search for LangGraph tutorials",
    "url": "https://www.google.com",
    "max_steps": 5,
    "require_confirmation": true
  }'
```

4. **Check task status**:

```bash
curl "http://localhost:8000/tasks/{task_id}"
```

## 💡 Example Usage

### Python Client

```python
import asyncio
from examples import WebOperatorClient

async def demo():
    client = WebOperatorClient()

    # Create a task
    task = await client.create_task(
        description="Search for 'web automation' on Google",
        url="https://www.google.com"
    )

    # Monitor progress
    result = await client.wait_for_completion_or_confirmation(task["task_id"])
    print(f"Result: {result}")

asyncio.run(demo())
```

### Curl Examples

```bash
# Create a Google search task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Search for Python tutorials on Google",
    "url": "https://www.google.com",
    "max_steps": 10
  }'

# Get task status
curl "http://localhost:8000/tasks/{task_id}"

# Confirm an action
curl -X POST "http://localhost:8000/tasks/{task_id}/confirm" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_id", "confirm": true}'
```

## 🛡️ Safety Features

- **User Confirmation**: Asks for approval before sensitive actions
- **Domain Safety**: Extra caution on financial/shopping sites
- **Action Validation**: Validates actions before execution
- **Screenshot Monitoring**: Visual evidence of all actions
- **Timeout Protection**: Prevents infinite loops
- **Error Recovery**: Attempts to recover from failures

## 🔌 API Endpoints

| Endpoint                   | Method | Description                       |
| -------------------------- | ------ | --------------------------------- |
| `/tasks`                   | POST   | Create a new automation task      |
| `/tasks/{task_id}`         | GET    | Get task status and details       |
| `/tasks/{task_id}/confirm` | POST   | Confirm or decline pending action |
| `/tasks`                   | GET    | List all tasks                    |
| `/tasks/{task_id}`         | DELETE | Cancel a running task             |
| `/screenshots/{filename}`  | GET    | Download screenshot               |
| `/health`                  | GET    | Health check                      |

## 🎯 Use Cases

### ✅ Supported Tasks

- **Web Research**: Search engines, article reading
- **Form Filling**: Contact forms, surveys
- **Data Extraction**: Scraping structured data
- **Navigation**: Multi-step website browsing
- **Content Creation**: Simple content generation tasks

### ⚠️ Limitations

- **No Financial Transactions**: Banking, payments blocked
- **No Personal Data**: Passwords, SSNs require manual input
- **Complex UIs**: Advanced JavaScript apps may have issues
- **CAPTCHA**: Requires human intervention

## 🔧 Advanced Configuration

### Custom Browser Settings

```python
# In tools/browser.py
BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-web-security',
    '--window-size=1920,1080'
]
```

### LLM Model Customization

```env
OPENAI_MODEL=gpt-4o-mini  # For faster, cheaper operations
OPENAI_MODEL=gpt-4o       # For complex reasoning
```

### Workflow Customization

```python
# Add custom nodes in nodes/
# Modify workflow.py to include new logic flows
```

## 📊 Monitoring

- **Logs**: Check `logs/operator.log`
- **Screenshots**: Available in `/screenshots/`
- **Metrics**: Prometheus endpoint at `/metrics`
- **Health**: Status at `/health`

## 🐛 Troubleshooting

### Common Issues

1. **Browser fails to start**:

   ```bash
   playwright install
   ```

2. **OpenAI API errors**:

   - Check API key in `.env`
   - Verify account has credits

3. **Task gets stuck**:

   - Check browser console for errors
   - Increase timeout values
   - Review screenshots for context

4. **Memory issues**:
   - Reduce max_steps
   - Close unused browser contexts

## 📈 Performance Tips

- Use `HEADLESS=true` for production
- Set appropriate `MAX_EXECUTION_TIME`
- Monitor memory usage with multiple tasks
- Use Redis for production state management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for the Operator concept inspiration
- **LangGraph** for agent orchestration
- **Playwright** for browser automation
- **FastAPI** for the web framework

---

**⚠️ Disclaimer**: This is an educational project. Use responsibly and respect website terms of service. Always obtain permission before automating interactions with websites.
