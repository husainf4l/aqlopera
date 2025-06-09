# 🚀 Web Operator Agent - Complete Setup Guide

## Overview

This is a complete implementation of a web automation agent similar to OpenAI's Operator, built with:

- **LangGraph**: For agent workflow orchestration
- **FastAPI**: For the REST API backend
- **Playwright**: For browser automation
- **OpenAI GPT-4o**: For intelligent decision making
- **Computer Vision**: For element detection and analysis

## 📋 Prerequisites

- Python 3.11+
- OpenAI API Key
- 4GB+ RAM recommended
- macOS, Linux, or Windows

## 🛠️ Installation Methods

### Method 1: Quick Start (Recommended)

```bash
# Clone/navigate to project
cd operator

# Run the setup script
./run.sh
```

The script will:

1. Create virtual environment
2. Install all dependencies
3. Install Playwright browsers
4. Set up configuration
5. Run tests
6. Start the server

### Method 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install

# 4. Setup configuration
cp .env.example .env
# Edit .env with your settings

# 5. Create directories
mkdir -p screenshots logs

# 6. Run tests
python test.py

# 7. Start server
python main.py
```

### Method 3: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or just the main service
docker build -t web-operator .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key web-operator
```

## ⚙️ Configuration

Edit `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional but recommended
OPENAI_MODEL=gpt-4o              # or gpt-4o-mini for faster/cheaper
BROWSER_TYPE=chromium            # chromium, firefox, webkit
HEADLESS=false                   # true for production
DEBUG=true                       # false for production
```

## 🎯 Quick Test

After setup, test the API:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Create a simple task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Go to httpbin.org and take a screenshot",
    "url": "https://httpbin.org",
    "max_steps": 3
  }'

# 3. Check task status (use task_id from step 2)
curl "http://localhost:8000/tasks/TASK_ID"
```

## 📖 Usage Examples

### Python Client

```python
import asyncio
from examples import WebOperatorClient

async def demo():
    client = WebOperatorClient()

    # Simple navigation task
    task = await client.create_task(
        description="Go to example.com and take a screenshot",
        url="https://example.com"
    )

    # Wait for completion
    result = await client.wait_for_completion_or_confirmation(task["task_id"])
    print(f"Task completed: {result}")

# Run the demo
asyncio.run(demo())
```

### Web Interface

1. Open http://localhost:8000/docs for interactive API docs
2. Use the Swagger UI to create and monitor tasks
3. View screenshots at http://localhost:8000/screenshots/

## 🛡️ Safety Features

The agent includes multiple safety layers:

1. **User Confirmation**: Asks before sensitive actions
2. **Domain Filtering**: Extra caution on financial sites
3. **Action Validation**: Validates each action before execution
4. **Timeout Protection**: Prevents infinite loops
5. **Screenshot Logging**: Visual record of all actions

## 🏗️ Architecture

```
Web Operator Agent
├── FastAPI Backend (api/)
│   ├── REST endpoints
│   ├── Task management
│   └── File serving
├── LangGraph Workflow (workflow.py)
│   ├── Task planning
│   ├── Action execution
│   └── Safety checks
├── Tools (tools/)
│   ├── Browser automation
│   ├── Computer vision
│   └── LLM integration
└── Nodes (nodes/)
    ├── Planning nodes
    ├── Execution nodes
    └── Control flow
```

## 📊 Monitoring

- **Logs**: `logs/operator.log`
- **Screenshots**: `screenshots/` directory
- **API Health**: `GET /health`
- **Task Status**: `GET /tasks/{task_id}`

## 🔧 Advanced Configuration

### Custom Models

```env
# Use different OpenAI models
OPENAI_MODEL=gpt-4o-mini     # Faster, cheaper
OPENAI_MODEL=gpt-4o          # More capable
OPENAI_MODEL=gpt-4-turbo     # Alternative
```

### Browser Settings

```env
# Browser configuration
BROWSER_TYPE=firefox         # Alternative browser
HEADLESS=true               # Run without GUI
BROWSER_TIMEOUT=60000       # Longer timeout
```

### Performance Tuning

```env
# Execution limits
MAX_EXECUTION_TIME=600      # 10 minute limit
MAX_STEPS=20               # More steps allowed
REQUESTS_PER_MINUTE=30     # Rate limiting
```

## 🐛 Troubleshooting

### Common Issues

1. **"Browser failed to launch"**

   ```bash
   playwright install --force
   ```

2. **"OpenAI API Error"**

   - Check API key in `.env`
   - Verify account has credits
   - Try different model

3. **"Module not found"**

   ```bash
   pip install -r requirements.txt
   export PYTHONPATH=/path/to/operator
   ```

4. **"Permission denied"**
   ```bash
   chmod +x run.sh
   ```

### Performance Issues

- Set `HEADLESS=true` for better performance
- Reduce `MAX_STEPS` for faster execution
- Use `gpt-4o-mini` for cheaper/faster responses
- Close unused browser tabs

### Memory Issues

```bash
# Monitor memory usage
docker stats  # For Docker
ps aux | grep python  # For native
```

## 📈 Production Deployment

### Environment Setup

```env
# Production settings
DEBUG=false
HEADLESS=true
LOG_LEVEL=WARNING
ENVIRONMENT=production

# Security
SECRET_KEY=your_production_secret_key
```

### Docker Production

```bash
# Build production image
docker build -t web-operator:prod .

# Run with production settings
docker run -d \
  --name web-operator \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e DEBUG=false \
  -e HEADLESS=true \
  web-operator:prod
```

### Scaling

- Use Redis for shared state
- Load balance multiple instances
- Monitor resource usage
- Implement request queuing

## 🔒 Security Considerations

1. **API Keys**: Never commit to version control
2. **Network**: Use HTTPS in production
3. **Rate Limiting**: Implement per-user limits
4. **Input Validation**: Sanitize all inputs
5. **Browser Security**: Run in sandboxed environment

## 📚 Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Playwright Documentation](https://playwright.dev/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy Automating! 🤖**
