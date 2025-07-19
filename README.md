# StealthStartup Multimodal RAG System

A sophisticated multimodal RAG (Retrieval-Augmented Generation) system that understands both text and images from documents using LlamaIndex, GPT-4V, and CLIP embeddings.

## 🚀 Features

### True Multimodal Understanding
- **Text Processing**: Extracts and chunks text content from PDFs
- **Image Understanding**: Uses GPT-4V to analyze and describe images in context
- **Table Extraction**: Processes tabular data from documents
- **Cross-Modal Retrieval**: Searches across text and images simultaneously

### Advanced AI Capabilities
- **GPT-4V Integration**: Visual understanding of charts, graphs, and diagrams
- **CLIP Embeddings**: Image embeddings for semantic search
- **LlamaIndex Framework**: Robust multimodal indexing and retrieval
- **Pinecone Vector Store**: Scalable vector storage for both text and images

### Voice Interface
- **Continuous Voice Input**: Automatic recording on site load
- **Real-time Transcription**: Live display of speech-to-text
- **Auto-Query Trigger**: Sends queries after 3-5 seconds of silence
- **Voice Status Indicators**: Visual feedback for recording states

### Modern Web Interface
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live transcription and response streaming
- **Source Visualization**: Displays text and image sources
- **Document Management**: Upload, view, and manage PDFs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│                 │    │                 │    │                 │
│ • React App     │◄──►│ • FastAPI       │◄──►│ • OpenAI GPT-4V │
│ • Voice Input   │    │ • LlamaIndex    │    │ • CLIP Embeddings│
│ • Real-time UI  │    │ • Pinecone      │    │ • GPT-4o        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Document Upload**: PDF files are uploaded and processed
2. **Multimodal Extraction**: Text, images, and tables are extracted
3. **GPT-4V Analysis**: Images are analyzed and described in context
4. **Vector Storage**: Text and image embeddings stored in Pinecone
5. **Query Processing**: User queries search across all modalities
6. **Response Generation**: LLM generates responses with multimodal context

## 📁 Project Structure

```
Stealthstartup/
├── backend/
│   ├── main.py                          # FastAPI application
│   ├── config.py                        # Configuration settings
│   ├── requirements.txt                  # Python dependencies
│   └── services/
│       ├── multimodal_processor.py      # PDF processing with GPT-4V
│       ├── multimodal_vector_store.py   # LlamaIndex + Pinecone
│       └── agent_service_simple.py      # Multimodal RAG agent
├── frontend/
│   ├── src/
│   │   ├── App.js                       # Main application
│   │   ├── components/                  # React components
│   │   ├── hooks/                       # Custom React hooks
│   │   └── services/                    # API services
│   └── package.json                     # Node.js dependencies
└── README.md                           # This file
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LlamaIndex**: Multimodal RAG framework
- **OpenAI**: GPT-4V and GPT-4o for text and vision
- **Pinecone**: Vector database for embeddings
- **PyMuPDF**: PDF processing and image extraction
- **Pillow**: Image processing

### Frontend
- **React**: Modern JavaScript framework
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **React Hot Toast**: Notification system
- **Web Speech API**: Voice input and transcription

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key
- Pinecone API key

### Backend Setup

1. **Clone and navigate to backend**:
```bash
cd Stealthstartup/backend
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp env_example.txt .env
# Edit .env with your API keys
```

4. **Start the backend server**:
```bash
python main.py
```

### Frontend Setup

1. **Navigate to frontend**:
```bash
cd Stealthstartup/frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the development server**:
```bash
npm start
```

## 🔧 Configuration

### Environment Variables (Backend)

Create a `.env` file in the backend directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=multimodal-rag
PINECONE_ENVIRONMENT=gcp-starter

# Deepgram Configuration (for voice)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Application Settings
UPLOAD_DIR=./uploads
FRONTEND_URL=http://localhost:3000
```

### LLM Parameters

The system supports configurable LLM parameters:

- **Temperature**: 0.7 (default) - Controls response creativity
- **Top P**: 0.9 (default) - Nucleus sampling parameter
- **Top K**: 40 (default) - Top-k sampling parameter
- **Max Tokens**: 4000 (default) - Maximum response length

Update via API: `POST /llm-parameters`

## 📊 Multimodal Processing Pipeline

### 1. Document Ingestion
```python
# PDF is uploaded and processed
document = await multimodal_processor.process_pdf_multimodal(file_path, filename)
```

### 2. Content Extraction
- **Text**: Extracted and chunked using sentence splitting
- **Images**: Extracted as PIL images and base64 encoded
- **Tables**: Extracted and converted to structured text

### 3. GPT-4V Analysis
```python
# Images are analyzed in context
enhanced_text = await processor.process_with_gpt4v(images, text)
```

### 4. Vector Storage
```python
# Text and image embeddings stored separately
text_store = PineconeVectorStore(namespace="text")
image_store = PineconeVectorStore(namespace="images")
```

### 5. Multimodal Retrieval
```python
# Search across both modalities
results = await vector_store.search_multimodal(query, top_k=5)
```

## 🎤 Voice Interface

### Continuous Voice Input
- Recording starts automatically on page load
- Real-time transcription displayed
- Automatic query sending after silence detection
- Visual status indicators for recording states

### Voice Processing Flow
1. **Audio Capture**: Browser microphone access
2. **Real-time Transcription**: Speech-to-text conversion
3. **Silence Detection**: Automatic query triggering
4. **Query Processing**: Multimodal RAG search
5. **Response Generation**: AI response with sources

## 🔍 API Endpoints

### Document Management
- `POST /upload` - Upload and process PDF with multimodal understanding
- `GET /health` - System health check
- `GET /index-stats` - Vector index statistics

### Query Processing
- `POST /query` - Process query with multimodal RAG
- `POST /query/stream` - Stream query response
- `POST /llm-parameters` - Update LLM parameters

### WebSocket
- `WS /ws` - Real-time communication for voice and chat

## 🎯 Usage Examples

### Upload a Document
```javascript
const formData = new FormData();
formData.append('file', pdfFile);
const response = await apiService.uploadDocument(formData);
```

### Query with Multimodal Understanding
```javascript
const result = await apiService.sendQuery("What charts are shown in the document?", "multimodal");
```

### Update LLM Parameters
```javascript
await apiService.updateLLMParameters({
  temperature: 0.8,
  top_p: 0.9,
  max_tokens: 3000
});
```

## 🔧 Development

### Adding New Modalities
1. Extend `MultimodalProcessor` to handle new content types
2. Add corresponding node types in LlamaIndex
3. Update vector store to handle new embeddings
4. Modify frontend to display new content types

### Customizing LLM Parameters
```python
# In agent_service_simple.py
multimodal_agent_service.update_llm_parameters(
    temperature=0.8,
    top_p=0.9,
    top_k=50,
    max_tokens=3000
)
```

### Extending Search Types
```python
# Add new search types in multimodal_vector_store.py
async def search_custom(self, query: str, modality: str):
    # Custom search implementation
    pass
```

## 🚀 Deployment

### Backend Deployment
1. Set up environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Start server: `python main.py`

### Frontend Deployment
1. Build for production: `npm run build`
2. Serve static files from build directory
3. Configure proxy to backend API

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🔍 Monitoring and Debugging

### Health Checks
- `GET /health` - Overall system health
- Check individual service status
- Monitor vector index statistics

### Logging
- Backend logs in console
- Frontend errors in browser console
- Voice processing status in UI

### Common Issues
1. **API Key Issues**: Verify OpenAI and Pinecone keys
2. **Voice Not Working**: Check microphone permissions
3. **Upload Failures**: Verify PDF format and size
4. **Search Issues**: Check vector index health

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LlamaIndex**: Multimodal RAG framework
- **OpenAI**: GPT-4V and GPT-4o models
- **Pinecone**: Vector database
- **React**: Frontend framework
- **FastAPI**: Backend framework

---

**Note**: This system represents a true multimodal RAG implementation that goes beyond simple text processing to understand and reason about both text and images in documents. 
