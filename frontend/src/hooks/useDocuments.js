import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

export const useDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/documents');
      setDocuments(response.data.documents);
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to fetch documents.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const uploadDocument = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    setError(null);
    const toastId = toast.loading('Uploading document...');

    try {
      const response = await axios.post('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success(response.data.message || 'Document uploaded successfully!', { id: toastId });
      await fetchDocuments();
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Upload failed.';
      setError(errorMessage);
      toast.error(errorMessage, { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (documentId) => {
    const toastId = toast.loading('Deleting document...');
    try {
      await axios.delete(`/api/documents/${documentId}`);
      toast.success('Document deleted.', { id: toastId });
      await fetchDocuments();
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to delete document.';
      toast.error(errorMessage, { id: toastId });
    }
  };

  return {
    documents,
    loading,
    error,
    uploadDocument,
    deleteDocument,
    refreshDocuments: fetchDocuments,
  };
}; 