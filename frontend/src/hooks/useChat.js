import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Generate a unique session ID for the user
    const newSessionId = uuidv4();
    setSessionId(newSessionId);

    // Initial welcome message from the assistant
    setMessages([
      {
        id: uuidv4(),
        role: 'assistant',
        content: "Hello! I'm your VoiceRAG assistant. Upload a PDF or ask me a question about the web. You can also use your voice!",
      },
    ]);
  }, []);
  
  const sendMessage = useCallback(async (text) => {
    if (!text || !sessionId) return;

    const userMessage = { id: uuidv4(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setSources([]);
    setError(null);

    const assistantMessageId = uuidv4();
    // Add a placeholder for the assistant's message
    setMessages((prev) => [...prev, { id: assistantMessageId, role: 'assistant', content: '' }]);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          session_id: sessionId,
          query: text,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An unknown error occurred');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const eventBoundary = '\n\n';
        while (buffer.includes(eventBoundary)) {
            const eventEndIndex = buffer.indexOf(eventBoundary);
            const eventData = buffer.substring(0, eventEndIndex);
            buffer = buffer.substring(eventEndIndex + eventBoundary.length);

            if (eventData.startsWith('data: ')) {
                const jsonString = eventData.substring(6);
                console.log('Received JSON:', jsonString);
                const chunk = JSON.parse(jsonString);
                console.log('Parsed chunk:', chunk);

                if (chunk.type === 'response') {
                    console.log('Adding response chunk:', chunk.data);
                    // Append content to the streaming message
                    setMessages(prev => prev.map(msg =>
                      msg.id === assistantMessageId ? { ...msg, content: msg.content + chunk.data } : msg
                    ));
                } else if (chunk.type === 'sources') {
                    console.log('Setting sources:', chunk.data);
                    // Set sources when received
                    setSources(chunk.data || []);
                } else if (chunk.type === 'error') {
                    console.log('Error received:', chunk.data);
                    // Handle error messages
                    const errorMessage = chunk.data || 'An error occurred';
                    setError(errorMessage);
                    toast.error(errorMessage);
                    setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
                }
            }
        }
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to get response from the assistant.';
      setError(errorMessage);
      toast.error(errorMessage);
      // Remove placeholder and add error message
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, setMessages, setIsLoading, setSources, setError]);

  const clearChat = useCallback(() => {
    // Reset chat to its initial state, keeping the session ID
    setMessages([
      {
        id: uuidv4(),
        role: 'assistant',
        content: "Hello! I'm your VoiceRAG assistant. Upload a PDF or ask me a question about the web. You can also use your voice!",
      },
    ]);
    setSources([]);
    setError(null);
    setIsLoading(false);
    toast.success('Chat cleared!');
  }, []);

  return {
    messages,
    isLoading,
    sources,
    sessionId,
    error,
    sendMessage,
    clearChat,
  };
}; 