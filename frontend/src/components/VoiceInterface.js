import React from 'react';

const VoiceInterface = ({ isRecording, transcript, onStartRecording, onStopRecording, isConnected, error }) => {
  const Icon = isRecording ? (
    // Stop Icon
    <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M6 6h12v12H6z" />
    </svg>
  ) : (
    // Microphone Icon
    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 10v2a7 7 0 01-14 0v-2" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19v4m0 0H9m3 0h3" />
    </svg>
  );

  const buttonClass = isRecording
    ? 'bg-red-500 hover:bg-red-600'
    : 'bg-blue-500 hover:bg-blue-600';

  return (
    <div className="flex flex-col items-center space-y-3">
      <button
        type="button"
        onClick={isRecording ? onStopRecording : onStartRecording}
        disabled={!isConnected}
        className={`p-4 rounded-full text-white transition-colors duration-200 transform hover:scale-105 ${buttonClass} disabled:bg-gray-400 shadow-lg`}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {Icon}
      </button>
      
      {/* Connection status */}
      {!isConnected && (
        <div className="text-sm text-gray-500 animate-pulse">Connecting to voice service...</div>
      )}
      
      {/* Recording indicator */}
      {isConnected && !isRecording && (
        <div className="text-sm text-gray-600">Click to start voice input</div>
      )}
      
      {/* Real-time transcript display */}
      {isRecording && transcript && (
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg text-sm text-gray-700 max-w-md text-center">
          <div className="font-semibold text-xs text-blue-600 mb-2 flex items-center justify-center">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2"></div>
            Listening...
          </div>
          <div className="text-gray-800">{transcript}</div>
        </div>
      )}
      
      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 p-3 rounded-lg text-sm text-red-700 max-w-md text-center">
          <div className="font-semibold text-xs text-red-600 mb-1">Voice Error</div>
          <div>{error}</div>
        </div>
      )}
    </div>
  );
};

export default VoiceInterface; 