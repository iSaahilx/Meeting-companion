import React, { useState, useEffect, useRef } from 'react';

const ImageViewer = ({ documentId, pageNumber, filename }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const imageRef = useRef(null);
  const containerRef = useRef(null);
  
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const imageUrl = `${baseUrl}/api/documents/${documentId}/page/${pageNumber}/image`;

  useEffect(() => {
    setLoading(true);
    setError(null);
    setImageLoaded(false);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [documentId, pageNumber]);

  const handleImageLoad = () => {
    console.log('Image loaded successfully:', imageUrl);
    setImageLoaded(true);
    setLoading(false);
    setError(null);
  };

  const handleImageError = (e) => {
    console.error('Image load error:', e, imageUrl);
    setError('Failed to load image');
    setLoading(false);
    setImageLoaded(false);
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.1));
  };

  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - pan.x,
        y: e.clientY - pan.y
      });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && zoom > 1) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.1, Math.min(5, prev * delta)));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        handleZoomIn();
      } else if (e.key === '-') {
        e.preventDefault();
        handleZoomOut();
      } else if (e.key === '0') {
        e.preventDefault();
        handleResetZoom();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const displayFilename = filename || `Page ${pageNumber}`;

  return (
    <div className="flex flex-col h-full bg-secondary-100">
      {/* Viewer Header */}
      <div className="p-3 bg-gray-50 border-b flex justify-between items-center">
        <span className="text-sm font-medium text-gray-700">
          {displayFilename}
        </span>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
            title="Zoom Out (-)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
            title="Zoom In (+)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <button
            onClick={handleResetZoom}
            className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
            title="Reset Zoom (0)"
          >
            Reset
          </button>
          <button
            onClick={() => window.open(imageUrl, '_blank')}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
            title="Open in New Tab"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </button>
          <a
            href={imageUrl}
            download={`${displayFilename}`}
            className="p-1 rounded hover:bg-gray-200 transition-colors"
            title="Download Image"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </a>
        </div>
      </div>

      {/* Image Container */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-hidden bg-gray-200 relative cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-gray-600">Loading image...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-2 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p className="text-red-600 font-medium">{error}</p>
              <p className="text-sm text-gray-500 mt-1">Please try again</p>
            </div>
          </div>
        )}

        {/* Image - always rendered but visibility controlled by CSS */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{
            transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
            transformOrigin: 'center center',
            opacity: imageLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease-in-out'
          }}
        >
          <img
            ref={imageRef}
            src={imageUrl}
            alt={`Page ${pageNumber}`}
            className="max-w-full max-h-full object-contain shadow-lg"
            onLoad={handleImageLoad}
            onError={handleImageError}
            draggable={false}
            style={{ userSelect: 'none' }}
          />
        </div>
      </div>

      {/* Footer with shortcuts */}
      <div className="p-2 bg-gray-50 border-t">
        <div className="flex justify-center text-xs text-gray-500 space-x-4">
          <span>Scroll to zoom</span>
          <span>Drag to pan</span>
          <span>+ / - to zoom</span>
          <span>0 to reset</span>
        </div>
      </div>
    </div>
  );
};

export default ImageViewer; 