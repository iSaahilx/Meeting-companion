import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';

export const useVoice = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  
  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const interimTranscriptRef = useRef('');
  const silenceTimerRef = useRef(null);
  const lastTranscriptTimeRef = useRef(Date.now());

  const connectWebSocket = useCallback(async () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Assuming the backend is running on port 8000 in development
      const host = process.env.NODE_ENV === 'production' 
        ? window.location.host 
        : `${window.location.hostname}:8000`;
      const wsUrl = `${protocol}//${host}/api/voice/stream`;
      
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected, readyState:', ws.readyState);
        setIsConnected(true);
        
        // Test if we can receive messages
        setTimeout(() => {
          console.log('WebSocket state after 1 second:', ws.readyState);
        }, 1000);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Voice WebSocket message:', data);
        
        if (data.type === 'transcript') {
          const { text, is_final } = data;
          
          // Update last transcript time
          lastTranscriptTimeRef.current = Date.now();
          
          if (is_final && text.trim()) {
            finalTranscriptRef.current += (text + ' ');
            interimTranscriptRef.current = '';
            setIsListening(false);
          } else {
            interimTranscriptRef.current = text;
            setIsListening(true);
          }

          const fullTranscript = finalTranscriptRef.current + interimTranscriptRef.current;
          setTranscript(fullTranscript);
          console.log(`Transcript updated: "${fullTranscript}" (final: ${is_final})`);
          
          // Reset silence timer on any transcript activity
          resetSilenceTimer();
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket connection error.');
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };

      socketRef.current = ws;
    } catch (err) {
      const errorMessage = 'Failed to connect to voice service.';
      setError(errorMessage);
      toast.error(errorMessage);
      console.error(err);
    }
  }, []);

  const clearTranscript = useCallback(() => {
    console.log('clearTranscript called - current transcript:', transcript);
    setTranscript('');
    finalTranscriptRef.current = '';
    interimTranscriptRef.current = '';
    setIsListening(false);
  }, [transcript]);

  const resetSilenceTimer = useCallback(() => {
    // Clear existing timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    
    // Set new timer for 3.5 seconds of silence
    silenceTimerRef.current = setTimeout(() => {
      console.log('Silence detected, triggering query...');
      const currentTranscript = finalTranscriptRef.current.trim();
      if (currentTranscript) {
        // Trigger the query callback
        if (window.onTranscriptComplete) {
          window.onTranscriptComplete(currentTranscript);
        }
        // Clear the transcript after triggering
        setTranscript('');
        finalTranscriptRef.current = '';
        interimTranscriptRef.current = '';
        setIsListening(false);
      }
    }, 3500); // 3.5 seconds
  }, []);

  const startRecording = useCallback(async () => {
    console.log('startRecording called - isRecording:', isRecording, 'isConnected:', isConnected);
    if (isRecording || !isConnected) {
      console.log('startRecording blocked - isRecording:', isRecording, 'isConnected:', isConnected);
      return;
    }
    
    setTranscript('');
    setError(null);
    finalTranscriptRef.current = '';
    interimTranscriptRef.current = '';
    console.log('Starting recording...');

    try {
      audioStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const supportedTypes = ['audio/wav', 'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg'];
      const supportedType = supportedTypes.find(type => MediaRecorder.isTypeSupported(type));

      if (!supportedType) {
        throw new Error('No supported audio format found.');
      }

      mediaRecorderRef.current = new MediaRecorder(audioStreamRef.current, {
        mimeType: supportedType,
      });

      mediaRecorderRef.current.addEventListener('dataavailable', (event) => {
        console.log('Audio data available:', event.data.size, 'bytes, WebSocket state:', socketRef.current?.readyState);
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          socketRef.current.send(event.data);
          console.log('Audio data sent to WebSocket');
        } else {
          console.log('Audio data NOT sent - size:', event.data.size, 'WebSocket state:', socketRef.current?.readyState);
        }
      });

      mediaRecorderRef.current.start(250); // a 250ms timeslice
      setIsRecording(true);
      console.log('MediaRecorder started, isRecording set to true');
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Could not start recording. Please check microphone permissions.');
      toast.error('Could not start recording. Please check microphone permissions.');
    }
  }, [isRecording, isConnected]);

  const stopRecording = useCallback(() => {
    console.log('stopRecording called - isRecording:', isRecording);
    if (!isRecording) return;
    
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'stop_recording' }));
    }

    mediaRecorderRef.current?.stop();
    audioStreamRef.current?.getTracks().forEach(track => track.stop());
    setIsRecording(false);
    console.log('Recording stopped');
  }, [isRecording]);

  // Auto-start recording when connected
  useEffect(() => {
    if (isConnected && !isRecording) {
      console.log('Auto-starting recording...');
      startRecording();
    }
  }, [isConnected, isRecording, startRecording]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      const socket = socketRef.current;
      // Only close the socket if it's open.
      if (socket && socket.readyState === WebSocket.OPEN) {
        console.log("Closing WebSocket connection.");
        socket.close();
      }
      socketRef.current = null;
      
      // Clear silence timer
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, [connectWebSocket]);

  return {
    isRecording,
    transcript,
    isConnected,
    isListening,
    error,
  };
}; 