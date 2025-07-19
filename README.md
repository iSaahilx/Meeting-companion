# StealthStartup: Voice-Powered RAG System

StealthStartup is an advanced Retrieval-Augmented Generation (RAG) application that allows users to ask questions about their documents using their voice. It transcribes the user's speech, finds the most relevant information within the uploaded documents, and generates a comprehensive, sourced answer using a large language model.

## Features

-   **Continuous Voice Input**: Automatic voice recording starts when the site loads, with real-time transcription display.
-   **Smart Query Triggering**: Automatically sends queries when speech stops for 3-5 seconds, providing a natural conversation flow.
-   **Real-time Transcription**: Shows live transcription as you speak, with visual indicators for listening status.
-   **Document Management**: Upload and manage a personal library of PDF documents.
-   **Advanced RAG Pipeline**: Utilizes a sophisticated pipeline including semantic chunking, vector search, and reranking to find the most accurate context.
-   **Sourced Answers**: Every answer is backed by citations from the source documents.
-   **Interactive Source Viewer**: View the exact page of a source document as an image, with zoom, pan, and download capabilities.
-   **Streaming Responses**: The AI's answer is streamed in real-time for a responsive feel.

## Tech Stack

| Category      | Technology                                                              |
|---------------|-------------------------------------------------------------------------|
| **Frontend**  | React, Tailwind CSS                                                     |
| **Backend**   | FastAPI (Python)                                                        |
| **AI/ML**     | OpenAI (GPT-4o), Deepgram (Speech-to-Text)             |
| **Database**  | Pinecone (Vector Store)                                                    |
| **PDF Parsing**| `unstructured.io`                                                       |

## End-to-End Workflow

The application follows a multi-step process to answer a user's question:

```mermaid
graph TD
    subgraph Frontend
        A[1. Auto-Start Recording] --> B[2. Real-time Transcription];
        B --> C[3. Speech Detection];
        C --> D{4. 3-5s Silence?};
        D -->|No| B;
        D -->|Yes| E[5. Send Query];
    end

    subgraph Backend
        E --> F[6. Transcribe with Deepgram];
        F --> G[7. Get User Query];
        G --> H[8. Document Search (Pinecone)];
        G --> I[9. Web Search (Serper.dev)];
        H --> J[10. Combine Top 5 from Each];
        I --> J;
        J --> K[11. Construct Prompt];
        K --> L[12. Generate Answer (OpenAI)];
    end

    subgraph Frontend
        L --> M[13. Stream Answer to UI];
        L --> N[14. Display Source Images];
    end

    style A fill:#cde4ff,stroke:#6a8ebf,stroke-width:2px
    style N fill:#cde4ff,stroke:#6a8ebf,stroke-width:2px
```

1.  **Auto-Start Recording**: Voice recording begins automatically when the site loads, with real-time transcription display.
2.  **Real-time Transcription**: The audio is continuously streamed to the backend, which uses the **Deepgram** API to provide live transcription.
3.  **Smart Query Triggering**: When speech stops for 3-5 seconds, the system automatically sends the completed transcript as a query.
4.  **Dual Search**: The transcribed question is used to perform **both** document search (using **Pinecone** vector store) and web search (using **Serper.dev** API) in parallel.
5.  **Result Combination**: The system takes the top 5 results from each source (documents and web) and combines them into a comprehensive context.
6.  **Generation**: The combined top 10 results (5 from documents + 5 from web) and the user's question are passed to the **OpenAI GPT-4o** model, which generates a synthesized answer.
7.  **Response & Sources**: The answer is streamed back to the UI, and links to the source pages are displayed for verification.

---

## Project Structure & File Guide

This section details the purpose of each key file in the project and where important configurations are located.

### Backend (`/backend`)

| File | Purpose | Key Configurations |
| --- | --- | --- |
| `main.py` | The main FastAPI application file. It defines all API endpoints for transcription, asking questions, document upload/deletion, and serving source images. | - API routes (`/api/transcribe`, `/api/ask`, etc.) |
| `services/agent_service_simple.py` | **The core of the RAG pipeline**. It orchestrates the flow from transcription to final answer generation. Always performs both document and web search. | - **LLM Model**: `gpt-4o` <br> - **Temperature**: `0.2` <br> - **Document Search**: Top 5 results from Pinecone <br> - **Web Search**: Top 5 results from Serper.dev <br> - **System Prompt**: The main instructions given to the LLM. |
| `services/vector_store.py` | Manages all interactions with the Pinecone vector database. Handles document indexing, embedding creation, similarity search, and deletion. | - **Vector Search**: Uses Pinecone for document similarity search |
| `services/pdf_processor.py`| Handles the ingestion and processing of uploaded PDF documents. It uses the `unstructured` library to partition PDFs into text, tables, and images. | - **Chunk Size**: `1024` characters <br> - **Chunk Overlap**: `200` characters |
| `config.py` | Loads all necessary API keys and configuration settings from a `.env` file using Pydantic. | - `OPENAI_API_KEY` <br> - `PINECONE_API_KEY` <br> - `SERPER_API_KEY` <br> - `DEEPGRAM_API_KEY` |
| `requirements.txt` | Contains all the Python dependencies required for the backend to run. | - `fastapi`, `uvicorn`, `python-dotenv`, `openai`, `pinecone-client`, `deepgram-sdk`, `unstructured`, etc. |

### Frontend (`/frontend`)

| File | Purpose |
| --- | --- |
| `src/App.js` | The root component of the React application. It manages the overall state and layout, including the visibility of the `PDFViewer` and `ImageViewer` modals. |
| `src/hooks/useVoice.js` | Manages continuous voice recording, real-time transcription, and automatic query triggering when speech stops for 3-5 seconds. |
| `src/components/ChatInterface.js`| Displays the conversation history between the user and the AI. It receives and renders the streaming response from the backend. **This is a voice-only app, so there is no text input field.** |
| `src/components/SourcePanel.js` | Displays the source documents that were used to generate an answer. It shows page images with links that open in the `ImageViewer`. |
| `src/components/ImageViewer.js` | A feature-rich modal for viewing source page images. It includes controls for zooming, panning, and downloading the image. |
| `src/components/DocumentList.js` | Displays the list of all uploaded documents, allowing users to view or delete them. |
| `src/services/api.js` | A utility file that centralizes all API `fetch` calls to the backend, making the code cleaner and easier to maintain. |
| `package.json` | Defines the frontend project's metadata, dependencies (like `react`, `tailwindcss`), and scripts (like `npm start`, `npm build`). |

## Setup and Installation

1.  **Clone the repository:**
```bash
git clone <repository-url>
    cd StealthStartup
```

2.  **Backend Setup:**
```bash
cd backend
python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
    ```

3.  **Frontend Setup:**
```bash
    cd ../frontend
npm install
    ```

4.  **Configuration:**
    -   In the `backend` directory, create a `.env` file by copying the `env_example.txt`.
    -   Fill in your API keys for OpenAI, Cohere, and Deepgram.
    ```
    OPENAI_API_KEY="sk-..."
    PINECONE_API_KEY="..."
    SERPER_API_KEY="..."
    DEEPGRAM_API_KEY="..."
    ```

## How to Run

1.  **Start the Backend Server:**
   ```bash
    cd backend
    uvicorn main:app --reload
    ```
    The backend will be running at `http://localhost:8000`.

2.  **Start the Frontend Development Server:**
   ```bash
    cd frontend
    npm start
    ```
    The frontend will open automatically at `http://localhost:3000`.

## How to Use

1.  **Upload Documents**: Use the "Upload" button to add PDF files to your knowledge base.
2.  **Start Speaking**: Voice recording begins automatically when the site loads. Simply start speaking to ask a question.
3.  **Natural Conversation**: Speak naturally - the system will automatically send your question when you pause speaking for 3-5 seconds.
4.  **View Answer and Sources**: The AI's answer will appear in the chat panel, and the source pages will appear in the right-hand panel.
5.  **Inspect Sources**: Click on any source image to open it in a full-screen viewer. 