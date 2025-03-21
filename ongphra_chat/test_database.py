import requests
import json
import uuid
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_conversation_state():
    """Test that conversation state is maintained across multiple requests."""
    print("Testing conversation state with MariaDB database...")
    
    # Generate a unique user ID for this test
    user_id = str(uuid.uuid4())
    print(f"Testing with user_id: {user_id}")
    
    try:
        # Create a new session
        session_url = f"{BASE_URL}{API_PREFIX}/chat/new-session"
        session_data = {
            "user_id": user_id,
            "title": "Test Conversation"
        }
        session_response = requests.post(session_url, json=session_data)
        session_data = session_response.json()
        
        if session_response.status_code != 200:
            print(f"Failed to create session: {session_data}")
            return
        
        session_id = session_data["session"]["id"]
        print(f"Created new session with ID: {session_id}")
        
        # Send first message
        print("===== First Message =====")
        chat_url = f"{BASE_URL}{API_PREFIX}/chat/message"
        message1 = "Hello, how are you today?"
        
        chat_data = {
            "message": message1,
            "user_id": user_id,
            "session_id": session_id,
            "stream": False
        }
        
        response1 = requests.post(chat_url, json=chat_data)
        result1 = response1.json()
        
        if response1.status_code != 200:
            print(f"Error: {result1}")
            return
        
        print(f"User: {message1}")
        print(f"Assistant: {result1['response']['choices'][0]['message']['content']}")
        print()
        
        # Send second message that references the first conversation
        print("===== Second Message =====")
        message2 = "What did I just ask you?"
        
        chat_data = {
            "message": message2,
            "user_id": user_id,
            "session_id": session_id,
            "stream": False
        }
        
        response2 = requests.post(chat_url, json=chat_data)
        result2 = response2.json()
        
        if response2.status_code != 200:
            print(f"Error: {result2}")
            return
        
        print(f"User: {message2}")
        print(f"Assistant: {result2['response']['choices'][0]['message']['content']}")
        print()
        
        # Get conversation history
        print("===== Conversation History =====")
        history_url = f"{BASE_URL}{API_PREFIX}/chat/history?session_id={session_id}"
        history_response = requests.get(history_url)
        history_data = history_response.json()
        
        if history_response.status_code != 200:
            print(f"Error retrieving history: {history_data}")
            return
        
        print(f"Number of messages in conversation: {len(history_data['messages'])}")
        for idx, msg in enumerate(history_data['messages']):
            print(f"[{idx+1}] {msg['role']}: {msg['content']}")
        
        # Verify that 4 messages were saved (2 user messages + 2 assistant responses)
        if len(history_data['messages']) == 4:
            print("\nTest PASSED: Conversation state was maintained correctly!")
        else:
            print(f"\nTest FAILED: Expected 4 messages, got {len(history_data['messages'])}")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    test_conversation_state() 