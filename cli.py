import requests
from groq import Groq
import warnings
import pygame
import os
import time
import wave
import pyaudio
from deepgram import DeepgramClient
from dotenv import load_dotenv
import sys
import shutil

load_dotenv()

BASE_URL = "http://localhost:8000"

conversation = []
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    print("Error: DEEPGRAM_API_KEY not found in .env")
    exit(1)

def print_colored(text: str, color_code: str):
    if text is None:
        return
    if os.name == 'nt':
        sys.stdout.write(f"\033[{color_code}m{text}\033[0m\n")
        sys.stdout.flush()
    else:
        print(f"\033[{color_code}m{text}\033[0m")

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
OUTPUT_FILENAME = "recording.wav"

def record_audio():
    p = pyaudio.PyAudio()

    prompt = "Press Enter to START recording or Type 'exit' to Exit the Session..."
    msg = get_input_and_replace(prompt = prompt)
    if msg.lower() == 'exit':
        return None

    record_prompt = "Recording... Speak now, Press Ctrl+C to STOP."
    print(record_prompt)
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            # Check if user pressed Enter (non-blocking way is tricky → we use a short sleep)
            time.sleep(0.1)  # small sleep so we can interrupt easily
    except KeyboardInterrupt:
        pass  # Ctrl+C also stops
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
    

        # Clear the recording prompt
        # Get terminal width
        terminal_width = shutil.get_terminal_size().columns
        
        # Calculate how many lines the prompt + input took
        total_length = len(record_prompt)
        lines_used = (total_length // terminal_width) + 1
        
        clear_prompt_lines(lines_used)
    

        # Save to WAV file
        wf = wave.open(OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # print(f"Saved recording to: {OUTPUT_FILENAME}")
        return OUTPUT_FILENAME


def transcribe_with_deepgram(audio_file):
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)

    # print("Transcribing...", end=" ", flush=True)

    with open(audio_file, "rb") as file:
        buffer_data = file.read()

    response = deepgram.listen.rest.v("1").transcribe_file(
        {"buffer": buffer_data, "mimetype": "audio/wav"},
        {
            "model": "nova-2",
            "smart_format": True,
            "language": "en",
        }
    )

    transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
    # print("Done.\n")
    # Delete the file after transcription
    os.remove(audio_file)
    return transcript.strip()



def get_session(session_id: str):
    """Retrieve session details and chat history"""
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    response.raise_for_status()
    return response.json()

def load_sessions():
    """Load all sessions"""
    response = requests.get(f"{BASE_URL}/sessions")
    response.raise_for_status()
    return response.json()

def create_session(session_name: str = None):
    """Create a new session"""
    payload = {"session_name": session_name} if session_name else {}
    response = requests.post(f"{BASE_URL}/sessions/create", json=payload)
    response.raise_for_status()
    return response.json()

def delete_session(session_id: str):
    """Delete a session"""
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    response.raise_for_status()
    return response.json()


def send_message(session_id: str, message: str, enable_history: bool = False):
    """Send a message to the session and get a response"""
    payload = {"query": message,
               "session_id": session_id,
               "enable_history": enable_history}
    response = requests.post(f"{BASE_URL}/query/chat", json=payload)
    response.raise_for_status()
    return response.json()

    
def show_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to the Voice Chat Client!")
        print("=================")
        print("1. Create new session")
        print("2. List sessions")
        print("3. Select session")
        print("4. Delete session")
        print("5. Exit")
        choice = input("Choose an option: ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            return choice
        else:
            print("Invalid option.")
            input("Press Enter to continue...")
    


def select_session():
    global conversation
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        sessions = load_sessions()
        print("Sessions:")
        for i in range(len(sessions)):
            print(f"- {i+1}, ID: {sessions[i]['id']}, Name: {sessions[i].get('session_name', 'N/A')}")
        print()
        session_number = input("Select session number: ").strip()
        try:
            session_index = int(session_number) - 1
            if session_index < 0 or session_index >= len(sessions):
                raise ValueError("Invalid session number")
            session_id = sessions[session_index]['id']
        except (ValueError, IndexError):
            print("Invalid session number.")
            input("Press Enter to continue...")
            continue

        session = get_session(session_id)
        if not session:
            print("Session not found.")
            input("Press Enter to continue...")
        else:
            print(f"Session: {session.get('session_name', 'N/A')} is now loaded.")
            conversation = session.get('messages', [])
            input("Press Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')
            return session_id

def clear_prompt_lines(lines_used: int):
    # Move cursor up by the number of lines used and clear them
    for _ in range(lines_used):
        sys.stdout.write('\033[A')  # Move up one line
        sys.stdout.write('\033[2K')  # Clear the line
    sys.stdout.flush()

def get_input_and_replace(prompt: str):
    """Get input and replace the prompt with just the user's text"""
    text = input(prompt)
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    
    # Calculate how many lines the prompt + input took
    total_length = len(prompt) + len(text)
    lines_used = (total_length // terminal_width) + 1
    
    clear_prompt_lines(lines_used)
    

    return text

def play_audio(text: str):
    client = Groq()
    response = client.audio.speech.create(
    model="canopylabs/orpheus-v1-english",
    voice="autumn",
    response_format="wav",
    input=text,
    )
    response.write_to_file("speech.wav")
        

    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module="pygame.pkgdata",
        message=".*pkg_resources is deprecated.*"
    )
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


    pygame.mixer.init()
    pygame.mixer.music.load("speech.wav")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)



def continue_conversation(user_input: str, session_id: str, enable_history: bool = True):
    print_colored(user_input, "92")
    print()
    conversation.append({"role": "human", "content": user_input})
    response = send_message(session_id, user_input, enable_history=enable_history)
    agent_response = response.get("response", "")
    conversation.append({"role": "ai", "content": agent_response})
    print_colored(agent_response, "93")
    return agent_response

def handle_voice_session(session_id: str):
    while True:
        try:
            audio_file = record_audio()
            if not audio_file:
                raise KeyboardInterrupt  # User cancelled recording
            transcript = transcribe_with_deepgram(audio_file)
            response = continue_conversation(transcript, session_id)
            play_audio(response)
        except KeyboardInterrupt:
            print("\nExiting voice session...")
            input("Press Enter to continue...")
            break

def handle_text_session(session_id: str):
    while True:
        prompt = "\nType your message (or 'exit' to go back): "
        user_input = get_input_and_replace(prompt)
        if user_input.lower() == 'exit':
            print("Exiting text session...")
            input("Press Enter to continue...")
            break

        continue_conversation(user_input, session_id)

def show_sub_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nSession Options:")
        print("a. Voice Session (record audio)")
        print("b. Text Session (type message)")
        print("c. Back to main menu")
        sub_choice = input("Choose an option: ").strip()
        os.system('cls' if os.name == 'nt' else 'clear')
        if sub_choice in ["a", "b", "c"]:
            if sub_choice in ["a", "b"]:
                load_conversation()
            return sub_choice
        else:
            print("Invalid option.")
            input("Press Enter to continue...")
        
def load_conversation():
    global conversation
    for msg in conversation:
        role = msg['role']
        content = msg['content']
        if role == 'human':
            print_colored(content, "92")
        elif role == 'ai':
            print_colored(content, "93")
        print()

if __name__ == "__main__":
    while True:
        choice = show_menu()
        os.system('cls' if os.name == 'nt' else 'clear')
        if choice == "1":
            name = input("Enter session name (or leave blank): ").strip()
            session = create_session(name if name else None)
            print(f"Created session: \n ID: {session['session_id']}\n Name: {session.get('session_name', 'N/A')}")
            input("Press Enter to continue...")

        elif choice == "2":
            sessions = load_sessions()
            print("Sessions:")
            for sess in sessions:
                print(f"- ID: {sess['id']}, Name: {sess.get('session_name', 'N/A')}")
            input("Press Enter to continue...")
        elif choice == "3":
            session_id = select_session()

            while True:
                sub_choice = show_sub_menu()
                if sub_choice == "a":
                    handle_voice_session(session_id)

                elif sub_choice == "b":
                    handle_text_session(session_id)

                elif sub_choice == "c":
                    break
                os.system('cls' if os.name == 'nt' else 'clear')

        elif choice == "4":
            session_id = input("Enter session ID to delete: ").strip()
            result = delete_session(session_id)
            print(f"Deleted session: {result}")
            input("Press Enter to continue...")
        elif choice == "5":
            print("Exiting. Goodbye!")
            break
