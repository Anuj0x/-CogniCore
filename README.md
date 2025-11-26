# AutoGPT Nexus 🤖

An intelligent autonomous AI agent powered by modern Python async architecture, featuring advanced memory systems, multi-LLM integration, and extensible action frameworks.

## ✨ Key Features

- **🚀 High-Performance Async Core**: Event-driven architecture with comprehensive async/await patterns delivering optimal concurrency and responsiveness
- **🧠 Cognitive Memory Engine**: Intelligent memory management featuring automated summarization, importance-weighted retrieval, and persistent state with vector search capabilities
- **🎯 Adaptive Reasoning Framework**: Dynamic decision-making with structured JSON prompting, multi-step reasoning chains, and continuous learning feedback loops
- **🔧 Modular Plugin Architecture**: Extensible design supporting custom actions, integrations, and specialized agent behaviors
- **📱 Unified Communication Hub**: Advanced Telegram integration with real-time messaging, command processing, and interactive agent control
- **🔍 Universal LLM Abstraction**: Multi-provider support for Ollama, OpenAI GPT, LMStudio, and oobabooga with automatic failover and load balancing
- **⚙️ Production-Ready Configuration**: Pydantic-powered configuration with environmental validation, hot-reloading, and secure credential management
- **📊 Enterprise Logging Stack**: Structured logging with multiple output streams, log rotation, and real-time monitoring capabilities
- **🧪 Industrial-Grade Testing**: Comprehensive test suite with async fixtures, integration mocking, and continuous deployment pipelines

## 🏗️ System Architecture

```
autogpt_nexus/
├── main.py                    # 🚀 Application bootstrap with graceful lifecycle management
├── core/                      # 🔧 System foundation layer
│   ├── config.py             # Pydantic configuration with environment validation
│   ├── logger.py             # Enterprise logging with structured output
│   └── agent.py              # Orchestration engine for agent behaviors
├── think/                    # 🧠 Cognitive processing layer
│   ├── modern_memory.py      # Vector-enhanced memory with summarization
│   └── modern_reasoning.py   # Decision-making with chain-of-thought prompting
├── action/                   # ⚡ Execution framework
│   └── modern_executor.py    # Async action registry with dependency injection
├── llm/                      # 🤖 Language model abstraction
│   └── provider.py           # Multi-provider LLM interface with resilience
├── integrations/             # 🌐 External service connectors
│   └── telegram.py           # Advanced Telegram bot with webhook support
├── assets/                   # 🎨 Static resources
└── test/                     # 🧪 Test harness with fixtures and mocks
```

## 🚀 Rapid Deployment

### System Requirements

- Python 3.9+ runtime environment
- Active LLM infrastructure (Ollama server recommended)
- PostgreSQL/Redis for advanced persistence (optional)

### Automated Installation

1. **Environment Preparation:**
   ```bash
   git clone https://github.com/Anuj0x/autogpt-nexus.git
   cd autogpt-nexus
   chmod +x setup.sh && ./setup.sh
   ```

2. **Configuration Setup:**
   ```bash
   cp .env.template .env
   # Configure your LLM endpoints and Telegram tokens
   nano .env
   ```

3. **System Launch:**
   ```bash
   ./run.sh
   ```

## ⚙️ Configuration

Create a `.env` file with your configuration:

```env
# LLM Configuration
LLM_SERVER_TYPE=ollama  # ollama, openai, lmstudio, oobabooga
LLM_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3

# Telegram (Optional)
TELEGRAM_API_KEY=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_NOTIFICATIONS=true

# Memory Settings
MEMORY_MAX_TOKENS=4000
MEMORY_AUTO_SUMMARIZE=true

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
```

## 🧠 Memory System

The advanced memory system provides:

- **Intelligent Storage**: Memories with importance scoring and metadata
- **Auto-Summarization**: Automatic summarization of old memories using LLM
- **Persistent Storage**: JSON-based persistence with backup
- **Context Retrieval**: Smart context building for decision making
- **Vector Search Ready**: Prepared for vector embeddings (optional)

## 🤖 Agent Capabilities

Built-in actions include:

- **observe**: Monitor environment and gather information
- **think**: Internal reflection and planning
- **search**: Web search using DuckDuckGo
- **communicate**: Send messages and interact
- **learn**: Store important information
- **analyze**: Break down complex information
- **wait**: Controlled pauses and timing

## 🔧 Extending the System

### Adding Custom Actions

```python
from action.modern_executor import ActionExecutor

async def my_custom_action(params):
    # Your action logic here
    return {"result": "success"}

# Register the action
executor = ActionExecutor(config)
await executor.register_action("my_action", my_custom_action)
```

### Adding LLM Providers

```python
from llm.provider import LLMProvider

class MyLLMProvider(LLMProvider):
    async def generate(self, prompt, **kwargs):
        # Your LLM integration here
        pass
```

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=mini_autogpt --cov-report=html
```

## 📦 Deployment

### Docker Deployment

```bash
# Build container
docker build -t mini-autogpt .

# Run container
docker run -p 3000:3000 mini-autogpt
```

### Systemd Service

See `setup.sh` for automated deployment.

## 🔒 Security

- API keys stored securely in environment variables
- Input validation with Pydantic models
- Rate limiting and error handling
- Secure communication with HTTPS APIs

## 📊 Monitoring

- Structured logging with configurable levels
- Health checks and status endpoints
- Performance metrics and timing
- Error tracking and reporting

## 👨‍💻 Creator

**Anuj0x** - [GitHub Profile](https://github.com/Anuj0x)

Expert in:
- Programming & Scripting Languages
- Deep Learning & State-of-the-Art AI Models
- Generative Models & Autoencoders
- Advanced Attention Mechanisms & Model Optimization
- Multimodal Fusion & Cross-Attention Architectures
- Reinforcement Learning & Neural Architecture Search
- AI Hardware Acceleration & MLOps
- Computer Vision & Image Processing
- Data Management & Vector Databases
- Agentic LLMs & Prompt Engineering
- Forecasting & Time Series Models
- Optimization & Algorithmic Techniques
- Blockchain & Decentralized Applications
- DevOps, Cloud & Cybersecurity
- Quantum AI & Circuit Design
- Web Development Frameworks
