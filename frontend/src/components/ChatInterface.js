import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatInterface = ({
  messages,
  loading,
  error,
  isRecording,
  transcript,
  isConnected,
  isListening,
  voiceError,
}) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const renderMessageContent = (content) => {
    return <ReactMarkdown>{content}</ReactMarkdown>;
  };

  return (
    <div className="flex flex-col h-full bg-secondary-100">
      {/* Messages Display */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-lg px-4 py-2 rounded-lg shadow ${
                message.role === 'user'
                  ? 'bg-primary-500 text-white'
                  : 'bg-white text-secondary-800'
              }`}
            >
              <div className="prose prose-sm max-w-none">
                {renderMessageContent(message.content)}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-lg px-4 py-2 rounded-lg shadow bg-white text-secondary-800">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse delay-75"></div>
                <div className="w-2 h-2 bg-secondary-400 rounded-full animate-pulse delay-150"></div>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="flex justify-center">
            <div className="px-4 py-2 rounded-lg bg-danger-100 text-danger-700">
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Real-time Voice Input Display */}
      <div className="p-4 bg-white border-t border-secondary-200">
        <div className="flex flex-col items-center space-y-3">
          {/* Connection Status */}
          {!isConnected && (
            <div className="text-sm text-gray-500 animate-pulse flex items-center">
              <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
              Connecting to voice service...
            </div>
          )}
          
          {/* Voice Status and Transcript */}
          {isConnected && (
            <div className="w-full max-w-2xl">
              {/* Voice Status Indicator */}
              <div className="flex items-center justify-center mb-3">
                <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
                  isListening 
                    ? 'bg-red-100 text-red-700' 
                    : isRecording 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-gray-100 text-gray-600'
                }`}>
                  <div className={`w-3 h-3 rounded-full ${
                    isListening 
                      ? 'bg-red-500 animate-pulse' 
                      : isRecording 
                        ? 'bg-blue-500' 
                        : 'bg-gray-400'
                  }`}></div>
                  <span className="text-sm font-medium">
                    {isListening 
                      ? 'Listening...' 
                      : isRecording 
                        ? 'Ready to listen' 
                        : 'Connecting...'
                    }
                  </span>
                </div>
              </div>
              
              {/* Real-time Transcript Display */}
              {transcript && (
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                  <div className="text-sm text-blue-600 mb-2 font-medium">
                    {isListening ? '🎤 Speaking...' : '📝 Final transcript'}
                  </div>
                  <div className="text-gray-800 text-lg leading-relaxed">
                    {transcript}
                  </div>
                  {isListening && (
                    <div className="mt-2 text-xs text-blue-500">
                      Speak naturally - your question will be sent automatically when you pause
                    </div>
                  )}
                </div>
              )}
              
              {/* Instructions when no transcript */}
              {!transcript && isRecording && (
                <div className="text-center text-gray-500 text-sm">
                  <div className="mb-2">🎤 Start speaking to ask a question</div>
                  <div className="text-xs">Your question will be sent automatically when you pause speaking</div>
                </div>
              )}
            </div>
          )}
          
          {/* Error Display */}
          {voiceError && (
            <div className="bg-red-50 border border-red-200 p-3 rounded-lg text-sm text-red-700 max-w-md text-center">
              <div className="font-semibold text-xs text-red-600 mb-1">Voice Error</div>
              <div>{voiceError}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 