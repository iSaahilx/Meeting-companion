# VoiceRAG Backend

FastAPI-based backend for the VoiceRAG application providing document processing, voice transcription, and intelligent search capabilities.

## Architecture

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management
├── services/               # Business logic services
│   ├── agent_service.py    # LangGraph-based intelligent agent
│   ├── agent_service_simple.py  # Simplified agent service
│   ├── pdf_processor.py    # PDF processing and chunking
│   ├── vector_store.py     # Pinecone vector database operations
│   ├── voice_service.py    # Deepgram voice transcription
│   └── web_search.py       # Serper web search integration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Features

- **Document Processing**: PDF upload, text extraction, and intelligent chunking
- **Vector Search**: Semantic search using OpenAI embeddings and Pinecone
- **Voice Transcription**: Real-time speech-to-text via Deepgram
- **Web Search**: Live search integration with Serper.dev
- **Intelligent Agent**: LangGraph-based decision making for query routing
- **Streaming Responses**: Real-time response generation

## Setup

### Prerequisites

- Python 3.8+
- API Keys:
  - OpenAI API key
  - Deepgram API key  
  - Pinecone API key
  - Serper.dev API key

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd voicerag/backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# Create .env file with your API keys (see Environment Variables section below)
# Use the template provided in the main README.md
```

5. **Start the server:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Environment Variables

Create a `.env` file with the following variables:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Pinecone Configuration
PINECONE_INDEX_NAME=voicerag-documents

# Application Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=50000000  # 50MB

# CORS Configuration
FRONTEND_URL=http://localhost:3000
```

## API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload and process PDF
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents/{id}/file` - Download document

### Chat Interface
- `POST /api/chat/stream` - Stream chat responses

### Voice Interface
- `WebSocket /api/voice/stream` - Real-time voice transcription

### System
- `GET /api/health` - Health check
- `GET /` - API status

## Services Overview

### PDFProcessor (`services/pdf_processor.py`)
- Handles PDF file upload and storage
- Extracts text, images, and tables from PDFs
- Creates intelligent chunks for vector storage
- Supports multimodal content processing

### VectorStore (`services/vector_store.py`)
- Manages Pinecone vector database operations
- Creates embeddings using OpenAI API
- Performs semantic search across documents
- Handles document metadata and retrieval

### VoiceService (`services/voice_service.py`)
- Real-time voice transcription via Deepgram
- WebSocket-based streaming audio processing
- Handles audio format conversion
- Provides transcription confidence scores

### WebSearchService (`services/web_search.py`)
- Live web search via Serper.dev API
- Parses and formats search results
- Supports news, image, and general web search
- Handles result ranking and filtering

### AgentService (`services/agent_service.py`)
- LangGraph-based intelligent agent
- Routes queries between document and web search
- Manages conversation history and context
- Streams responses in real-time

## Configuration

The application uses Pydantic settings for configuration management. Key settings include:

- **OpenAI**: Model selection, embedding dimensions
- **Deepgram**: Voice model and language settings
- **Pinecone**: Index configuration and search parameters
- **Application**: File upload limits, CORS settings

## Development

### Running Tests
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Deployment

### Using Docker
```bash
# Build image
docker build -t voicerag-backend .

# Run container
docker run -p 8000:8000 --env-file .env voicerag-backend
```

### Environment Variables for Production
- Set `DEBUG=False`
- Configure proper CORS origins
- Use production-grade database URLs
- Set up proper logging configuration

## Health Checks

The `/api/health` endpoint provides status information for all services:
- Vector store connectivity
- PDF processor status
- Voice service availability
- Agent service health

## Logging

The application uses Python's built-in logging module. Log levels can be configured via environment variables:
- `LOG_LEVEL=INFO` (default)
- `LOG_LEVEL=DEBUG` for detailed debugging

## Security Considerations

- API keys are loaded from environment variables
- File uploads are validated and size-limited
- CORS is configured for specific origins
- Input validation is performed on all endpoints

## Performance

- Async/await pattern for non-blocking operations
- Streaming responses for real-time user experience
- Efficient vector search with configurable similarity thresholds
- Connection pooling for external API calls

## Troubleshooting

### Common Issues

1. **"No API key provided"**: Check your `.env` file
2. **"Pinecone index not found"**: Index will be created automatically
3. **"File upload failed"**: Check file size and format
4. **"WebSocket connection failed"**: Verify Deepgram API key

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your environment for detailed logging.

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for public methods
4. Write tests for new functionality
5. Update this README for significant changes 