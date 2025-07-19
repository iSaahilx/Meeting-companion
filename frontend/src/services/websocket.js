class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageHandlers = new Map();
    this.mediaRecorder = null;
    this.audioChunks = [];
  }

  connect(url = null) {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = url || this.getWebSocketURL();
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    this.isConnected = false;
    this.stopRecording();
  }

  getWebSocketURL() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_URL || 
                 (process.env.NODE_ENV === 'development' ? 'localhost:8000' : window.location.host);
    return `${protocol}//${host}/ws/voice`;
  }

  attemptReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      this.connect().catch(() => {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('Max reconnection attempts reached');
          this.emit('maxReconnectAttemptsReached');
        }
      });
    }, delay);
  }

  on(event, handler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event).add(handler);
  }

  off(event, handler) {
    if (this.messageHandlers.has(event)) {
      this.messageHandlers.get(event).delete(handler);
    }
  }

  emit(event, data = null) {
    if (this.messageHandlers.has(event)) {
      this.messageHandlers.get(event).forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }

  handleMessage(data) {
    const { type } = data;
    
    switch (type) {
      case 'connection_established':
        this.emit('connected', data);
        break;
      case 'transcript':
        this.emit('transcript', data);
        break;
      case 'recording_started':
        this.emit('recordingStarted', data);
        break;
      case 'recording_stopped':
        this.emit('recordingStopped', data);
        break;
      case 'error':
        this.emit('error', data);
        break;
      case 'speech_final':
        this.emit('speechFinal', data);
        break;
      case 'utterance_end':
        this.emit('utteranceEnd', data);
        break;
      default:
        console.warn('Unknown message type:', type);
    }
  }

  send(data) {
    if (this.socket && this.isConnected) {
      if (typeof data === 'object') {
        this.socket.send(JSON.stringify(data));
      } else {
        this.socket.send(data);
      }
    } else {
      console.warn('WebSocket not connected');
    }
  }

  sendBinary(data) {
    if (this.socket && this.isConnected) {
      this.socket.send(data);
    } else {
      console.warn('WebSocket not connected');
    }
  }

  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1
        } 
      });

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
          
          // Convert to the format expected by the backend
          event.data.arrayBuffer().then(buffer => {
            this.sendBinary(buffer);
          });
        }
      };

      this.mediaRecorder.onstart = () => {
        this.send({ type: 'start_recording' });
        this.emit('recordingStarted');
      };

      this.mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        this.send({ type: 'stop_recording' });
        this.emit('recordingStopped');
      };

      // Start recording with small chunks for real-time processing
      this.mediaRecorder.start(100); // 100ms chunks
      
    } catch (error) {
      console.error('Error starting recording:', error);
      this.emit('error', { message: 'Failed to start recording: ' + error.message });
      throw error;
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
      this.mediaRecorder = null;
    }
  }

  getConnectionState() {
    return {
      isConnected: this.isConnected,
      readyState: this.socket ? this.socket.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService; 