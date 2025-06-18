"""
Voice Interface for Minerva

This module provides voice recognition and speech synthesis capabilities
for the Minerva AI Assistant, enabling natural voice interaction.
"""

import os
import sys
import threading
import queue
from typing import Optional, Callable, Dict, Any
from loguru import logger

# Note: The following imports require the packages to be installed
# speech_recognition, pyttsx3, and pyaudio
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    logger.warning("Voice packages not installed. Voice interface will be disabled.")
    VOICE_ENABLED = False

class VoiceInterface:
    """Voice interface for Minerva AI Assistant."""
    
    def __init__(self, 
                 wake_word: str = "minerva",
                 voice_id: Optional[str] = None,
                 rate: int = 175,
                 volume: float = 1.0):
        """
        Initialize the voice interface.
        
        Args:
            wake_word: Word to activate voice listening
            voice_id: Voice ID for speech synthesis
            rate: Speech rate
            volume: Speech volume (0.0 to 1.0)
        """
        self.wake_word = wake_word.lower()
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        
        self.is_listening = False
        self.recognizer = None
        self.engine = None
        self.microphone = None
        
        # Command queue for processing recognized commands
        self.command_queue = queue.Queue()
        
        # Callback for handling commands
        self.command_callback = None
        
        # Set up voice if available
        if VOICE_ENABLED:
            self._setup_voice()
    
    def _setup_voice(self):
        """Set up voice recognition and synthesis components."""
        try:
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            
            # Initialize text-to-speech engine
            self.engine = pyttsx3.init()
            
            # Set voice properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            else:
                # Try to set a good default voice
                voices = self.engine.getProperty('voices')
                if voices:
                    # Prefer female voice if available
                    female_voices = [v for v in voices if 'female' in v.name.lower()]
                    if female_voices:
                        self.engine.setProperty('voice', female_voices[0].id)
                    else:
                        self.engine.setProperty('voice', voices[0].id)
            
            logger.info("Voice interface initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing voice interface: {str(e)}")
            self.recognizer = None
            self.engine = None
    
    def list_available_voices(self) -> Dict[str, Any]:
        """
        List all available voices for speech synthesis.
        
        Returns:
            Dictionary of available voices
        """
        if not VOICE_ENABLED or not self.engine:
            return {"error": "Voice interface not available"}
        
        voices = {}
        for idx, voice in enumerate(self.engine.getProperty('voices')):
            voices[voice.id] = {
                "name": voice.name,
                "languages": voice.languages,
                "gender": "female" if "female" in voice.name.lower() else "male",
                "age": voice.age
            }
        
        return voices
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice for speech synthesis.
        
        Args:
            voice_id: ID of the voice to use
            
        Returns:
            True if successful
        """
        if not VOICE_ENABLED or not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.voice_id = voice_id
            return True
        except Exception as e:
            logger.error(f"Error setting voice: {str(e)}")
            return False
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        if not VOICE_ENABLED or not self.engine:
            logger.warning(f"Voice disabled, would say: {text}")
            return False
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Error speaking: {str(e)}")
            return False
    
    def listen(self) -> Optional[str]:
        """
        Listen for speech and convert to text.
        
        Returns:
            Recognized text or None if not recognized
        """
        if not VOICE_ENABLED or not self.recognizer:
            return None
        
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                # Listen for speech
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                logger.info("Processing speech...")
                
                # Convert speech to text
                text = self.recognizer.recognize_google(audio)
                
                logger.info(f"Recognized: {text}")
                return text
                
        except sr.WaitTimeoutError:
            logger.info("No speech detected")
        except sr.UnknownValueError:
            logger.info("Speech not understood")
        except sr.RequestError as e:
            logger.error(f"Error with speech recognition service: {str(e)}")
        except Exception as e:
            logger.error(f"Error listening: {str(e)}")
        
        return None
    
    def start_listening(self, callback: Callable[[str], None]) -> bool:
        """
        Start continuous listening in background.
        
        Args:
            callback: Function to call with recognized text
            
        Returns:
            True if started successfully
        """
        if not VOICE_ENABLED or not self.recognizer:
            return False
        
        if self.is_listening:
            return True
        
        self.command_callback = callback
        self.is_listening = True
        
        # Start listening thread
        threading.Thread(target=self._listen_loop, daemon=True).start()
        
        return True
    
    def _listen_loop(self):
        """Background listening loop."""
        logger.info("Starting continuous listening loop")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                
                while self.is_listening:
                    try:
                        logger.debug("Listening for commands...")
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        
                        try:
                            text = self.recognizer.recognize_google(audio).lower()
                            logger.info(f"Heard: {text}")
                            
                            # Check for wake word
                            if self.wake_word in text:
                                # Extract the command (everything after the wake word)
                                command = text.split(self.wake_word, 1)[1].strip()
                                if command:
                                    logger.info(f"Command detected: {command}")
                                    
                                    # Add to command queue
                                    self.command_queue.put(command)
                                    
                                    # Call callback if provided
                                    if self.command_callback:
                                        self.command_callback(command)
                                else:
                                    # Just the wake word was spoken
                                    self.speak("Yes, how can I help you?")
                            
                        except sr.UnknownValueError:
                            pass  # Speech not understood
                        except sr.RequestError as e:
                            logger.error(f"Error with speech recognition service: {str(e)}")
                            
                    except sr.WaitTimeoutError:
                        pass  # No speech detected, continue listening
                    
        except Exception as e:
            logger.error(f"Error in listening loop: {str(e)}")
            self.is_listening = False
    
    def stop_listening(self) -> bool:
        """
        Stop continuous listening.
        
        Returns:
            True if stopped successfully
        """
        self.is_listening = False
        return True
    
    def get_next_command(self) -> Optional[str]:
        """
        Get the next command from the queue.
        
        Returns:
            Next command or None if queue is empty
        """
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None
    
    def wait_for_command(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Wait for the next command from the queue.
        
        Args:
            timeout: Maximum time to wait (in seconds), or None to wait indefinitely
            
        Returns:
            Next command or None if timeout expires
        """
        try:
            return self.command_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
