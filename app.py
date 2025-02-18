import speech_recognition as sr
import pyttsx3 as access
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import warnings
warnings.filterwarnings("ignore")

class EnhancedSpeechRecognition:
    def __init__(self):
        # Initialize recognizer
        self.recognizer = sr.Recognizer()
        
        # Optimized settings for better recognition
        self.recognizer.energy_threshold = 3000  # Increased for better noise handling
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Increased for better phrase completion
        self.recognizer.phrase_threshold = 0.5
        self.recognizer.non_speaking_duration = 0.5
        
    def get_voice_input(self, timeout=5, retry_count=3):
        """Get voice input with improved recognition"""
        for attempt in range(retry_count):
            try:
                with sr.Microphone() as source:
                    print(f"\nListening... (Attempt {attempt + 1}/{retry_count})")
                    
                    # Dynamic noise adjustment
                    if attempt == 0:
                        print("Adjusting for ambient noise...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    # Get audio input
                    try:
                        audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
                    except sr.WaitTimeoutError:
                        print("No speech detected. Please try again.")
                        continue
                    
                    try:
                        # Try Google Speech Recognition
                        text = self.recognizer.recognize_google(audio)
                        if text.strip():
                            print("You said:", text)
                            return text.lower()
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                    
                    if attempt < retry_count - 1:
                        print("Please try again...")
                        
            except Exception as e:
                print(f"Error in voice input: {str(e)}")
                if attempt < retry_count - 1:
                    print("Retrying...")
                continue
                
        return None

class SpotifyVoiceController:
    def __init__(self):
        # Spotify API credentials
        self.SPOTIFY_CLIENT_ID = "your client id of spotify"
        self.SPOTIFY_CLIENT_SECRET = "your secret id spotify"
        self.REDIRECT_URI = "http://localhost:8888/callback"
        self.scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
        
        # Initialize Spotify client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.SPOTIFY_CLIENT_ID,
            client_secret=self.SPOTIFY_CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI,
            scope=self.scope
        ))
        
        # Initialize text-to-speech
        self.engine = access.init()
        self.engine.setProperty('rate', 150)  # Adjusted for better clarity
        
        # Initialize speech recognition
        self.speech_recognizer = EnhancedSpeechRecognition()
        
        # Initialize feedback messages
        self.feedback_messages = {
            'not_understood': "I didn't understand that command. Please try again.",
            'processing': "Processing your command...",
            'no_song_name': "Please specify a song name to play.",
            'searching': "Searching for your song..."
        }
        
        # Command mapping with expanded variations
        self.commands = {
            'volume_up': ['increase', 'volume up', 'increase volume', 'louder', 'turn it up', 
                         'raise volume', 'make it louder', 'boost volume', 'higher'],
            'volume_down': ['decrease', 'volume down', 'decrease volume', 'softer', 'quieter', 
                           'lower volume', 'make it quieter', 'reduce volume', 'lower'],
            'pause': ['pause', 'stop', 'pause music', 'stop music', 'pause the music', 
                     'stop playing', 'halt', 'freeze', 'shut up'],
            'play': ['play', 'resume', 'start', 'continue', 'unpause', 'start music', 
                    'continue playing', 'resume music', 'go'],
            'next': ['next', 'next song', 'skip', 'skip song', 'next track', 
                    'forward', 'skip forward', 'change song'],
            'previous': ['previous', 'previous song', 'go back', 'last song', 
                        'back', 'skip back', 'earlier song'],
            'exit': ['exit', 'quit', 'close', 'stop program', 'bye', 'goodbye', 
                    'end', 'terminate', 'stop app'],
            'current': ['what is playing', 'what song is this', 'current song', 
                       'now playing', 'tell me the song', 'what is this song']
        }

    def speak_feedback(self, message, wait=True):
        """Provide voice feedback with option to not wait"""
        print(f"Speaking message: {message}")
        try:
            self.engine.say(message)
            if wait:
                self.engine.runAndWait()
        except Exception as e:
            print(f"Error speaking message: {str(e)}")

    def get_active_device(self):
        """Get active Spotify device"""
        try:
            devices = self.sp.devices()
            if not devices['devices']:
                return None
            
            # First try to get the active device
            active_device = next((device for device in devices['devices'] if device['is_active']), None)
            if active_device:
                return active_device
                
            # If no active device, return the first available one
            return devices['devices'][0]
        except Exception as e:
            print(f"Error getting device: {str(e)}")
            return None

    def adjust_volume(self, increase=True):
        """Adjust volume with improved feedback"""
        try:
            current_playback = self.sp.current_playback()
            if current_playback and 'device' in current_playback:
                current_volume = current_playback['device']['volume_percent']
                new_volume = min(current_volume + 10, 100) if increase else max(current_volume - 10, 0)
                self.sp.volume(new_volume)
                message = f"Volume {'increased' if increase else 'decreased'} to {new_volume}%"
                print(message)
                self.speak_feedback(message)
                return True
            else:
                print("No active playback found")
                self.speak_feedback("No active playback found")
                return False
        except Exception as e:
            print(f"Error adjusting volume: {str(e)}")
            return False

    def pause_playback(self):
        """Pause playback with improved error handling"""
        try:
            device = self.get_active_device()
            if device:
                self.sp.pause_playback(device_id=device['id'])
                print("Music paused successfully")
                self.speak_feedback("Music paused")
                return True
            else:
                print("No active device found")
                self.speak_feedback("No active device found")
                return False
        except Exception as e:
            print(f"Error pausing playback: {str(e)}")
            return False

    def resume_playback(self):
        """Resume playback with improved error handling"""
        try:
            device = self.get_active_device()
            if device:
                self.sp.start_playback(device_id=device['id'])
                print("Music resumed successfully")
                self.speak_feedback("Music resumed")
                return True
            else:
                print("No active device found")
                self.speak_feedback("No active device found")
                return False
        except Exception as e:
            print(f"Error resuming playback: {str(e)}")
            return False

    def play_song(self, song_name):
        """Play specific song with improved search and feedback"""
        if not song_name:
            self.speak_feedback(self.feedback_messages['no_song_name'])
            return False
            
        print(f"\nSearching for: {song_name}")
        self.speak_feedback(self.feedback_messages['searching'], wait=False)
        
        try:
            # Get active device
            device = self.get_active_device()
            if not device:
                print("No active Spotify device found!")
                self.speak_feedback("No active Spotify device found")
                return False

            # Search for the song
            results = self.sp.search(q=song_name, limit=5, type='track')
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                self.sp.start_playback(device_id=device['id'], uris=[track['uri']])
                
                message = f"Playing {track['name']} by {track['artists'][0]['name']}"
                print("\n" + message)
                self.speak_feedback(message)
                return True
            else:
                message = f"Sorry, I couldn't find the song: {song_name}"
                print("\n" + message)
                self.speak_feedback(message)
                return False

        except Exception as e:
            print(f"Error playing song: {str(e)}")
            self.speak_feedback("Sorry, there was an error playing the song")
            return False

    def get_current_track_info(self):
        """Get current track information with improved error handling"""
        try:
            current_playback = self.sp.current_playback()
            if current_playback and current_playback.get('item'):
                track = current_playback['item']
                artists = ", ".join([artist['name'] for artist in track['artists']])
                
                message = f"Now playing {track['name']} by {artists}"
                print(message)
                try:
                    self.speak_feedback(message)
                except Exception as e:
                    print(f"Error speaking track info: {str(e)}")
                return message
            return "No track currently playing"
        except Exception as e:
            return f"Error getting track info: {str(e)}"

    def process_command(self, command):
        """Process voice commands with improved feedback"""
        if not command:
            self.speak_feedback(self.feedback_messages['not_understood'])
            return True

        command = command.lower().strip()
        print(f"\nProcessing command: '{command}'")
        
        # Exit command
        if any(exit_cmd in command for exit_cmd in self.commands['exit']):
            self.speak_feedback("Goodbye!")
            return False

        try:
            # Volume up
            if any(vol_up in command for vol_up in self.commands['volume_up']):
                print("Increasing volume...")
                self.adjust_volume(increase=True)

            # Volume down
            elif any(vol_down in command for vol_down in self.commands['volume_down']):
                print("Decreasing volume...")
                self.adjust_volume(increase=False)

            # Pause
            elif any(pause_cmd in command for pause_cmd in self.commands['pause']):
                print("Pausing playback...")
                self.pause_playback()

            # Play specific song or resume
            elif any(play_cmd in command for play_cmd in self.commands['play']):
                if len(command.split()) > 1:
                    # Extract song name by removing the play command
                    song_name = command
                    for cmd in self.commands['play']:
                        song_name = song_name.replace(cmd, '').strip()
                    self.play_song(song_name)
                else:
                    print("Resuming playback...")
                    self.resume_playback()

            # Next track
            elif any(next_cmd in command for next_cmd in self.commands['next']):
                print("Skipping to next track...")
                self.sp.next_track()
                self.speak_feedback("Next track", wait=False)

            # Previous track
            elif any(prev_cmd in command for prev_cmd in self.commands['previous']):
                print("Going to previous track...")
                self.sp.previous_track()
                self.speak_feedback("Previous track", wait=False)

            # Current track info
            elif any(current_cmd in command for current_cmd in self.commands['current']):
                track_info = self.get_current_track_info()
                print(track_info)
                self.speak_feedback(track_info)

            # Command not recognized
            else:
                print("Command not recognized.")
                self.speak_feedback(self.feedback_messages['not_understood'])
                self.show_available_commands()

        except Exception as e:
            print(f"Error processing command: {str(e)}")
            self.speak_feedback("Sorry, there was an error processing your command")

        return True

    def show_available_commands(self):
        """Show available commands to the user"""
        print("\nAvailable commands:")
        print("- Play a song: 'play [song name]'")
        print("- Control playback: 'play', 'pause', 'next', 'previous'")
        print("- Volume: 'volume up', 'volume down'")
        print("- Current track: 'what is playing', 'current song'")
        print("- Exit: 'quit', 'exit'")

    def start(self):
        """Start the voice controller with improved error handling"""
        print("\nInitializing Spotify Voice Controller...")
        print("Checking Spotify connection...")
        
        # Test Spotify connection
        try:
            self.sp.current_user()
            print("Successfully connected to Spotify!")
        except Exception as e:
            print(f"Error connecting to Spotify: {str(e)}")
            print("Please check your credentials and internet connection.")
            return
        
        print("\nSpotify Voice Controller is ready!")
        print("Speak your commands clearly. Say 'exit' or 'quit' to stop.")
        self.speak_feedback("Ready for commands", wait=False)
        
        while True:
            try:
                # Get voice input
                command = self.speech_recognizer.get_voice_input()
                if not self.process_command(command):
                    break
                    
            except KeyboardInterrupt:
                print("\nProgram interrupted by user")
                break
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                continue

if __name__ == "__main__":
    try:
        controller = SpotifyVoiceController()
        controller.start()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        print("\nThank you for using Spotify Voice Controller!")
