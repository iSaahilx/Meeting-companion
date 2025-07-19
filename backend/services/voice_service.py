# Updated to use the event-driven Deepgram SDK
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from fastapi import WebSocket
from deepgram import DeepgramClient, LiveTranscriptionEvents
import websockets
from config import settings

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.deepgram = DeepgramClient(settings.deepgram_api_key)
        self.active_connections: Dict[str, WebSocket] = {}

    async def handle_voice_stream(self, websocket: WebSocket):
        """Handle real-time voice transcription via WebSocket using a queue."""
        connection_id = id(websocket)
        self.active_connections[connection_id] = websocket
        logger.info(f"New voice stream connection: {connection_id}")

        # This queue will hold messages from Deepgram's thread
        message_queue: asyncio.Queue = asyncio.Queue()

        def on_message(self_ignored, result, **kwargs):
            """Event handler for Deepgram's transcript messages."""
            try:
                message_queue.put_nowait(result)
            except Exception as e:
                logger.error(f"Error putting message in queue: {e}")

        def on_error(self_ignored, error, **kwargs):
            """Event handler for Deepgram errors."""
            logger.error(f"Deepgram error: {error}")
            message_queue.put_nowait(error)

        try:
            # Initialize the Deepgram connection
            deepgram_connection = self.deepgram.listen.websocket.v("1")
            deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)

            options = {
                "model": "nova-2-general",
                "language": "en-US",
                "encoding": "opus",
                "interim_results": True,
                "punctuate": True,
                "smart_format": True,
            }
            
            # Correctly call the synchronous start method
            if not deepgram_connection.start(options):
                logger.error("Failed to start Deepgram connection.")
                raise Exception("Failed to start Deepgram connection")
            
            logger.info("Deepgram connection started successfully")

            # Task to send keepalive messages to Deepgram
            async def keepalive_task():
                try:
                    while True:
                        logger.debug("Sending keepalive to Deepgram.")
                        deepgram_connection.keep_alive()
                        await asyncio.sleep(4)  # Send keepalive every 4 seconds
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Keepalive task error: {e}")

            keepalive_task_handle = asyncio.create_task(keepalive_task())

            # Task to send messages from the queue to the client
            async def send_task():
                while True:
                    message = await message_queue.get()
                    if message is None:  # Sentinel value to end task
                        break
                    await self.process_deepgram_message(websocket, message)

            send_task_handle = asyncio.create_task(send_task())

            # Main loop to receive audio from client and send to Deepgram
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    logger.info("Client disconnected.")
                    break

                if "bytes" in message:
                    deepgram_connection.send(message["bytes"])
                elif "text" in message:
                    data = json.loads(message["text"])
                    if data.get("type") == "stop_recording":
                        logger.info("Stop recording signal received from client.")
                        # This doesn't stop the main loop, just signals Deepgram
                        # to finalize the current utterance. The connection remains open.

            # Cleanup
            await message_queue.put(None)  # End the send_task
            send_task_handle.cancel()
            
            # Correctly call the synchronous finish method
            deepgram_connection.finish()
            logger.info("Deepgram connection finished.")

        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Client connection closed normally.")
        except Exception as e:
            logger.error(f"Voice stream error: {e}", exc_info=True)
        finally:
            if 'keepalive_task_handle' in locals():
                keepalive_task_handle.cancel()
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            logger.info(f"Voice stream handler for {connection_id} finished.")


    async def process_deepgram_message(self, websocket: WebSocket, data):
        """Process transcription message from Deepgram"""
        try:
            logger.info(f"Processing Deepgram message: {type(data)} - {str(data)[:200]}...")
            
            # Handle LiveResultResponse objects directly
            if hasattr(data, 'channel') and data.channel:
                alternatives = data.channel.alternatives
                if alternatives and len(alternatives) > 0:
                    transcript_data = alternatives[0]
                    text = transcript_data.transcript
                    confidence = transcript_data.confidence
                    
                    # Get is_final from the result
                    is_final = getattr(data, 'is_final', False)
                    if not is_final and hasattr(data, 'metadata') and data.metadata:
                        is_final = getattr(data.metadata, 'is_final', False)
                    
                    logger.info(f"Transcript: '{text}' (confidence: {confidence}, is_final: {is_final})")

                    if text.strip():
                        message = {
                            "type": "transcript",
                            "text": text,
                            "confidence": confidence,
                            "is_final": is_final,
                            "timestamp": getattr(data, 'start', 0)
                        }
                        logger.info(f"Sending transcript message to frontend: {message}")
                        await websocket.send_json(message)
                        if is_final:
                            logger.info(f"Final transcript sent to frontend: {text}")

            # Handle special message types
            if hasattr(data, 'type'):
                message_type = data.type
                if message_type == "UtteranceEnd":
                     await websocket.send_json({
                        "type": "utterance_end",
                        "message": "Utterance ended"
                    })
                     logger.info("Utterance end signal sent to frontend.")
                elif message_type == "SpeechFinal":
                     await websocket.send_json({
                        "type": "speech_final",
                        "message": "Speech segment completed"
                    })

        except Exception as e:
            logger.error(f"Error processing Deepgram message: {e}", exc_info=True)

    async def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe a pre-recorded audio file"""
        try:
            with open(audio_file_path, "rb") as audio:
                source = {"buffer": audio, "mimetype": "audio/wav"}
                
                options = {
                    "model": "nova-2",
                    "language": settings.deepgram_language,
                    "punctuate": True,
                    "smart_format": True,
                    "diarize": True,
                    "utterances": True
                }
                
                response = await self.deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
                
                # Extract transcript
                transcript = ""
                confidence = 0.0
                
                if response and "results" in response:
                    channels = response["results"].get("channels", [])
                    if channels:
                        alternatives = channels[0].get("alternatives", [])
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "")
                            confidence = alternatives[0].get("confidence", 0.0)
                
                return {
                    "transcript": transcript,
                    "confidence": confidence,
                    "full_response": response
                }
                
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            raise

    def health_check(self) -> bool:
        """Check if voice service is healthy"""
        try:
            # Check if Deepgram API key is configured
            return bool(settings.deepgram_api_key)
        except:
            return False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        return {
            "active_connections": len(self.active_connections),
            "connection_ids": list(self.active_connections.keys())
        } 