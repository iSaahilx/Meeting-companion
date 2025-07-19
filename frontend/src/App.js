import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import PDFViewer from './components/PDFViewer';
import ImageViewer from './components/ImageViewer';
import SourcePanel from './components/SourcePanel';
import { useVoice } from './hooks/useVoice';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [showPDFViewer, setShowPDFViewer] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [selectedImageSource, setSelectedImageSource] = useState(null);

  // Custom hooks for managing application state
  const {
    isRecording,
    transcript,
    isConnected,
    isListening,
    error: voiceError
  } = useVoice();

  const {
    documents,
    loading: documentsLoading,
    error: documentsError,
    uploadDocument,
    deleteDocument,
    refreshDocuments
  } = useDocuments();

  const {
    messages,
    isLoading: chatLoading,
    sources,
    sessionId,
    sendMessage,
    clearChat,
    error: chatError
  } = useChat();

  // Set up global callback for transcript completion
  useEffect(() => {
    window.onTranscriptComplete = (finalTranscript) => {
      console.log('Transcript completed, sending message:', finalTranscript);
      if (finalTranscript.trim()) {
        sendMessage(finalTranscript);
      }
    };

    return () => {
      window.onTranscriptComplete = null;
    };
  }, [sendMessage]);

  // Handle source clicks to show relevant pages
  const handleSourceClick = (source) => {
    if (source.type === 'document') {
      // For page images (JPG), show image viewer
      if (source.page_image_data && source.page_image_url) {
        setSelectedImageSource(source);
        setShowImageViewer(true);
      } else {
        // For regular document sources, open PDF viewer
        setSelectedDocument(source.document_id);
        setSelectedPage(source.page_number);
        setShowPDFViewer(true);
      }
    } else if (source.type === 'web') {
      window.open(source.url, '_blank');
    }
  };

  // Handle document selection from document list
  const handleDocumentSelect = (document) => {
    setSelectedDocument(document.document_id);
    setSelectedPage(1);
    setShowPDFViewer(true);
  };

  return (
    <div className="flex h-screen bg-secondary-50">
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:inset-0
      `}>
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="flex items-center justify-between p-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Documents</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md hover:bg-secondary-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Document Upload */}
          <div className="p-4 border-b border-secondary-200">
            <DocumentUpload
              onUpload={uploadDocument}
              loading={documentsLoading}
              error={documentsError}
            />
          </div>

          {/* Document List */}
          <div className="flex-1 overflow-y-auto">
            <DocumentList
              documents={documents}
              loading={documentsLoading}
              error={documentsError}
              onDocumentSelect={handleDocumentSelect}
              onDocumentDelete={deleteDocument}
              onRefresh={refreshDocuments}
            />
          </div>
        </div>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-80">
        {/* Header */}
        <Header 
          onMenuClick={() => setSidebarOpen(true)}
          onClearChat={clearChat}
          sessionId={sessionId}
          isConnected={isConnected}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat Interface takes the main space */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <ChatInterface
              messages={messages}
              loading={chatLoading}
              error={chatError}
              isRecording={isRecording}
              transcript={transcript}
              isConnected={isConnected}
              isListening={isListening}
              voiceError={voiceError}
            />
          </div>

          {/* Sources Panel */}
          {sources && sources.length > 0 && (
            <div className="w-80 border-l border-secondary-200 bg-white overflow-y-auto">
              <SourcePanel
                sources={sources}
                onSourceClick={handleSourceClick}
              />
            </div>
          )}
        </div>
      </div>

      {/* PDF Viewer Modal */}
      {showPDFViewer && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-full max-h-[90vh] flex flex-col">
            {/* PDF Viewer Header */}
            <div className="flex items-center justify-between p-4 border-b border-secondary-200">
              <h3 className="text-lg font-semibold text-secondary-900">
                Document Viewer
              </h3>
              <button
                onClick={() => setShowPDFViewer(false)}
                className="p-2 rounded-md hover:bg-secondary-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* PDF Viewer Content */}
            <div className="flex-1 overflow-hidden">
              <PDFViewer
                documentId={selectedDocument}
                initialPage={selectedPage}
                highlightPage={selectedPage}
              />
            </div>
          </div>
        </div>
      )}

      {/* Image Viewer Modal */}
      {showImageViewer && selectedImageSource && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-full max-h-[90vh] flex flex-col">
            {/* Image Viewer Header */}
            <div className="flex items-center justify-between p-4 border-b border-secondary-200">
              <h3 className="text-lg font-semibold text-secondary-900">
                Image Viewer
              </h3>
              <button
                onClick={() => setShowImageViewer(false)}
                className="p-2 rounded-md hover:bg-secondary-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Image Viewer Content */}
            <div className="flex-1 overflow-hidden">
              <ImageViewer
                documentId={selectedImageSource.document_id}
                pageNumber={selectedImageSource.page_number}
                filename={selectedImageSource.filename}
              />
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#1e293b',
            border: '1px solid #e2e8f0',
            borderRadius: '0.5rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  );
}

export default App; 