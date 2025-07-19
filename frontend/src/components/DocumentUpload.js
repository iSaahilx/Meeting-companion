import React, { useState, useRef } from 'react';

const DocumentUpload = ({ onUpload, loading, error }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
      setSelectedFile(null);
      if(fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };
  
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  }

  return (
    <div>
      <div 
        onClick={triggerFileSelect} 
        className="flex justify-center items-center w-full px-6 py-10 border-2 border-dashed rounded-lg cursor-pointer border-secondary-300 hover:border-primary-500 hover:bg-secondary-100 transition-colors"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          disabled={loading}
        />
        <div className="text-center">
          {selectedFile ? (
            <>
              <p className="text-sm text-secondary-600">Selected file:</p>
              <p className="font-semibold text-primary-700">{selectedFile.name}</p>
            </>
          ) : (
            <>
              <svg className="mx-auto h-12 w-12 text-secondary-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <p className="mt-1 text-sm text-secondary-600">
                <span className="font-semibold text-primary-600">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-secondary-500">PDF up to 10MB</p>
            </>
          )}
        </div>
      </div>
      
      <button
        onClick={handleUpload}
        disabled={!selectedFile || loading}
        className="w-full mt-4 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:bg-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        {loading ? 'Uploading...' : 'Upload Document'}
      </button>

      {error && <p className="text-sm text-danger-500 mt-2">Upload Error: {error}</p>}
    </div>
  );
};

export default DocumentUpload; 