import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Try multiple worker configurations
try {
  // Method 1: Direct CDN
  pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
} catch (e) {
  try {
    // Method 2: Unpkg CDN
    pdfjs.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js';
  } catch (e2) {
    console.error('Failed to set PDF.js worker:', e2);
  }
}

const PDFViewer = ({ documentId, initialPage, highlightPage }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(initialPage || 1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [useIframe, setUseIframe] = useState(false);
  
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const pdfUrl = `${baseUrl}/api/documents/${documentId}/file`;

  // console.log('PDFViewer props:', { documentId, initialPage, highlightPage });
  // console.log('PDF URL:', pdfUrl);

  useEffect(() => {
    setPageNumber(highlightPage || initialPage || 1);
  }, [highlightPage, initialPage]);

  useEffect(() => {
    // console.log('PDFViewer mounted, documentId:', documentId);
    if (!documentId) {
      console.error('No documentId provided to PDFViewer');
      setError('No document ID provided');
      setLoading(false);
    }
  }, [documentId]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    console.log('PDF loaded successfully:', numPages, 'pages');
    setNumPages(numPages);
    setLoading(false);
  };

  const onDocumentLoadError = (error) => {
    console.error('PDF load error:', error);
    setError(`Error loading PDF: ${error.message}`);
    setLoading(false);
    // Auto-fallback to iframe after 3 seconds
    setTimeout(() => {
      console.log('Falling back to iframe viewer');
      setUseIframe(true);
      setError(null);
    }, 3000);
  }

  const goToPrevPage = () => setPageNumber(prev => Math.max(prev - 1, 1));
  const goToNextPage = () => setPageNumber(prev => Math.min(prev + 1, numPages));



  return (
    <div className="flex flex-col h-full bg-secondary-100">
      {/* Viewer mode toggle */}
      <div className="p-2 bg-gray-50 border-b flex justify-between items-center">
        <span className="text-sm text-gray-600">Document Viewer</span>
        <button onClick={() => setUseIframe(!useIframe)} className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded transition-colors">
          {useIframe ? 'Enhanced View' : 'Browser View'}
        </button>
      </div>
      
      {loading && <div className="text-center p-4">Loading PDF...</div>}
      {error && <div className="text-center p-4 text-danger-500">{error}</div>}
      
      {/* Iframe fallback viewer */}
      {useIframe && (
        <div className="flex-1">
          <iframe
            src={pdfUrl}
            className="w-full h-full border-0"
            title="PDF Document"
            onLoad={() => {
              console.log('PDF loaded in iframe');
              setLoading(false);
              setError(null);
            }}
            onError={(e) => {
              console.error('Iframe error:', e);
              setError('Failed to load PDF in iframe');
            }}
          />
        </div>
      )}
      
      {/* React-PDF viewer */}
      {!useIframe && (
        <div className="flex-1 overflow-y-auto">
          
          {!error && (
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              onLoadProgress={({ loaded, total }) => {
                console.log('PDF loading progress:', loaded, '/', total);
              }}
              onSourceSuccess={() => {
                console.log('PDF source loaded successfully');
              }}
              onSourceError={(error) => {
                console.error('PDF source error:', error);
              }}
              loading={<div className="text-center p-4">Loading PDF document...</div>}
              error={<div className="text-center p-4 text-red-500">Failed to load PDF</div>}
              className="flex justify-center"
            >
              <Page
                pageNumber={pageNumber}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className={pageNumber === highlightPage ? "border-4 border-primary-500" : ""}
                onLoadSuccess={() => {
                  console.log('Page loaded successfully');
                }}
                onLoadError={(error) => {
                  console.error('Page load error:', error);
                }}
              />
            </Document>
          )}
        </div>
      )}

      {numPages && (
        <div className="flex items-center justify-center p-2 bg-white border-t">
          <button onClick={goToPrevPage} disabled={pageNumber <= 1} className="px-3 py-1 mr-2 rounded-md bg-secondary-200 disabled:opacity-50">
            Prev
          </button>
          <span>
            Page {pageNumber} of {numPages}
          </span>
          <button onClick={goToNextPage} disabled={pageNumber >= numPages} className="px-3 py-1 ml-2 rounded-md bg-secondary-200 disabled:opacity-50">
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default PDFViewer; 