import React from 'react';

const DocumentList = ({ documents, loading, error, onDocumentSelect, onDocumentDelete, onRefresh }) => {
  const handleDelete = (documentId, filename) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      onDocumentDelete(documentId);
    }
  };

  const truncateFilename = (filename, maxLength = 35) => {
    if (filename.length <= maxLength) return filename;
    const extension = filename.split('.').pop();
    const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...';
    return truncatedName + '.' + extension;
  };

  if (loading && documents.length === 0) {
    return (
      <div className="p-4 text-center text-secondary-500">
        <p>Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-danger-500">
        <p>Error loading documents: {error}</p>
        <button
          onClick={onRefresh}
          className="mt-2 px-3 py-1 bg-primary-500 text-white text-sm rounded-md hover:bg-primary-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-secondary-500">
        <p>No documents uploaded yet.</p>
        <p className="text-sm">Upload a PDF to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 p-4">
      {documents.map((doc) => (
        <div
          key={doc.document_id}
          className="group flex items-center p-3 rounded-md bg-white hover:bg-primary-50 transition-colors border border-gray-200"
        >
          <div 
            className="flex-1 cursor-pointer min-w-0 pr-3"
            onClick={() => onDocumentSelect(doc)}
          >
            <p 
              className="font-medium text-secondary-800 group-hover:text-primary-700 truncate"
              title={doc.filename}
            >
              {truncateFilename(doc.filename)}
            </p>
            <p className="text-sm text-secondary-500">
              {doc.chunk_count || doc.page_count || 0} chunks
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation(); // prevent row click
              handleDelete(doc.document_id, doc.filename);
            }}
            className="flex-shrink-0 p-2 rounded-md text-red-400 hover:bg-red-100 hover:text-red-600 transition-colors"
            title="Delete document"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
};

export default DocumentList; 