import React, { useState } from 'react';

const SourcePanel = ({ sources, onSourceClick }) => {
  const [imageLoadErrors, setImageLoadErrors] = useState({});
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const handleImageError = (sourceIndex) => {
    setImageLoadErrors(prev => ({
      ...prev,
      [sourceIndex]: true
    }));
  };

  const handleImageLoad = (sourceIndex) => {
    setImageLoadErrors(prev => ({
      ...prev,
      [sourceIndex]: false
    }));
  };

  const renderDocumentContent = (source, index) => {
    const chunkType = source.chunk_type || 'text';
    
    // For sources with page_image_data, show the page image instead of text
    if (source.page_image_data && source.page_image_url) {
      return (
        <div className="mb-3">
          
          {!imageLoadErrors[index] ? (
            <img
              src={`${baseUrl}${source.page_image_url}`}
              alt={`Page ${source.page_number} from ${source.filename}`}
              className="max-w-full h-auto rounded-lg border border-gray-200 shadow-sm"
              style={{ maxHeight: '400px' }}
              onError={() => handleImageError(index)}
              onLoad={() => handleImageLoad(index)}
            />
          ) : (
            <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 text-center">
              <div className="text-gray-500 mb-2">
                <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Could not load page image</p>
            </div>
          )}
        </div>
      );
    }
    
    // For image chunks, show the extracted image
    if (chunkType === 'image' && source.image_data) {
      return (
        <div className="mb-3">
          <div className="text-xs text-blue-600 font-medium mb-2">🖼️ Extracted Image</div>
          <img
            src={`data:image/png;base64,${source.image_data}`}
            alt={`Extracted image from page ${source.page_number}`}
            className="max-w-full h-auto rounded-lg border border-gray-200 shadow-sm"
            style={{ maxHeight: '250px' }}
            onError={() => handleImageError(index)}
            onLoad={() => handleImageLoad(index)}
          />
        </div>
      );
    }
    
    // For image chunks that have large images (not stored in metadata)
    if (chunkType === 'image' && source.has_large_image && source.chunk_id) {
      return (
        <div className="mb-3">
          <div className="text-xs text-blue-600 font-medium mb-2">🖼️ Extracted Image</div>
          {!imageLoadErrors[index] ? (
            <img
              src={`${baseUrl}/api/chunks/${source.chunk_id}/image`}
              alt={`Extracted image from page ${source.page_number}`}
              className="max-w-full h-auto rounded-lg border border-gray-200 shadow-sm"
              style={{ maxHeight: '250px' }}
              onError={() => handleImageError(index)}
              onLoad={() => handleImageLoad(index)}
            />
          ) : (
            <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 text-center">
              <div className="text-gray-500 mb-2">
                <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-sm text-gray-600">Could not load extracted image</p>
            </div>
          )}
        </div>
      );
    }
    
    // For table chunks, show structured data
    if (chunkType === 'table') {
      return (
        <div className="mb-3">
          <div className="text-xs text-green-600 font-medium mb-2">📊 Table Data</div>
          <div className="bg-gray-50 p-3 rounded-lg border text-sm">
            <p className="text-secondary-800 italic">
              "{source.content.substring(0, 300)}..."
            </p>
          </div>
        </div>
      );
    }
    
    // For text chunks or fallback, show text content
    return (
      <div className="mb-3">
        <div className="text-xs text-gray-600 font-medium mb-2">📄 Text Content</div>
        <div className="bg-gray-50 p-3 rounded-lg border">
          <p className="text-sm text-secondary-800 italic">
            "{source.content.substring(0, 200)}..."
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-secondary-900">Sources</h3>
      </div>
      <div className="flex-1 overflow-y-auto">
        <ul className="divide-y divide-secondary-200">
          {sources.map((source, index) => (
            <li
              key={index}
              onClick={() => onSourceClick(source)}
              className="p-4 hover:bg-secondary-100 cursor-pointer"
            >
              {source.type === 'document' && (
                <div>
                  <div className="text-sm text-secondary-600 mb-3 flex items-center justify-between">
                    <span>Page {source.page_number}</span>
                    {source.chunk_type && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        {source.page_image_data ? 'image' : source.chunk_type}
                      </span>
                    )}
                  </div>
                  
                  {/* Dynamic content based on chunk type */}
                  {renderDocumentContent(source, index)}
                </div>
              )}
              
              {source.type === 'web' && (
                <div>
                  <div className="font-semibold text-primary-700">
                    🌐 Web Result
                  </div>
                  <div className="text-sm text-secondary-600 pl-5 truncate">
                    {source.url}
                  </div>
                  <p className="text-sm text-secondary-800 mt-1 pl-5 italic">
                    "{source.content}"
                  </p>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default SourcePanel; 