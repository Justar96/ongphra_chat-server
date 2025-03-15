# examples/chat_interface.py
import asyncio
import json
import httpx
import os
import time
from datetime import datetime
from typing import Dict, Optional, List, Any

API_URL = "http://localhost:8000/fortune"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class FortuneTellerChat:
    """Simple chat interface for the Thai Fortune Teller API"""
    
    def __init__(self):
        self.user_info = {
            "birth_date": None,
            "thai_day": None,
            "language": "thai"
        }
        self.session_id = None
        self.conversation_history = []
        self.response_cache = {}  # Cache for responses
    
    async def send_message(self, message: str) -> str:
        """Send a message to the fortune teller API and get a response"""
        
        # Check if this is a command to set birth information
        if message.startswith("/birth "):
            return self._set_birth_info(message[7:])
        
        # Check if this is a language command
        if message == "/english":
            self.user_info["language"] = "english"
            return "Language set to English."
        elif message == "/thai":
            self.user_info["language"] = "thai"
            return "ตั้งค่าภาษาเป็นภาษาไทยแล้ว"
        elif message == "/history":
            return self._show_history()
        elif message == "/clear":
            self.conversation_history = []
            self.response_cache = {}
            return "Conversation history and cache cleared."
        
        # Check if we have this message in cache
        cache_key = f"{message}_{self.user_info['language']}_{self.user_info['birth_date']}_{self.user_info['thai_day']}"
        if cache_key in self.response_cache:
            print("Using cached response")
            fortune_text = self.response_cache[cache_key]
            
            # Add to conversation history
            self._add_to_history(message, fortune_text)
            
            return fortune_text
        
        # Regular question to the fortune teller
        async with httpx.AsyncClient() as client:
            # Prepare request payload
            payload = {
                "question": message,
                "language": self.user_info["language"]
            }
            
            # Add birth info if available
            if self.user_info["birth_date"] and self.user_info["thai_day"]:
                payload["birth_date"] = self.user_info["birth_date"]
                payload["thai_day"] = self.user_info["thai_day"]
            
            # Send request to API with retries
            print(f"Sending request to {API_URL} with payload: {payload}")
            
            for attempt in range(MAX_RETRIES):
                try:
                    # Use session cookies to maintain the conversation context
                    cookies = {}
                    if self.session_id:
                        cookies["session_id"] = self.session_id
                    
                    response = await client.post(API_URL, json=payload, cookies=cookies, timeout=30.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Save the session ID
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                    
                    # Extract the fortune text
                    fortune_text = data["fortune"]
                    
                    # Cache the response
                    self.response_cache[cache_key] = fortune_text
                    
                    # Add to conversation history
                    self._add_to_history(message, fortune_text)
                    
                    print(f"Received response: {data}")
                    return fortune_text
                except httpx.HTTPStatusError as e:
                    error_detail = "Unknown error"
                    try:
                        error_json = e.response.json()
                        error_detail = error_json.get('detail', str(e))
                    except Exception:
                        error_detail = f"Status code: {e.response.status_code}, Response: {e.response.text}"
                    
                    if attempt < MAX_RETRIES - 1:
                        print(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {error_detail}. Retrying...")
                        time.sleep(RETRY_DELAY)
                    else:
                        return f"Error: {error_detail}"
                except httpx.RequestError as e:
                    if attempt < MAX_RETRIES - 1:
                        print(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}. Retrying...")
                        time.sleep(RETRY_DELAY)
                    else:
                        return f"Connection error: {str(e)}"
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        print(f"Unexpected error (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}. Retrying...")
                        time.sleep(RETRY_DELAY)
                    else:
                        return f"An error occurred: {str(e)}"
    
    def _add_to_history(self, user_message: str, assistant_response: str):
        """Add messages to conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep history to a reasonable size
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]
    
    def _set_birth_info(self, birth_info: str) -> str:
        """Set the user's birth information"""
        try:
            parts = birth_info.split()
            if len(parts) < 2:
                return "Please provide both birth date (YYYY-MM-DD) and Thai day."
            
            birth_date, thai_day = parts[0], parts[1]
            
            # Validate birth date format
            datetime.strptime(birth_date, "%Y-%m-%d")
            
            # Validate Thai day
            valid_days = [
                "อาทิตย์", "จันทร์", "อังคาร", "พุธ", 
                "พฤหัสบดี", "ศุกร์", "เสาร์"
            ]
            if thai_day not in valid_days:
                return f"Invalid Thai day. Please use one of: {', '.join(valid_days)}"
            
            # Set the user info
            self.user_info["birth_date"] = birth_date
            self.user_info["thai_day"] = thai_day
            
            # Clear cache when birth info changes
            self.response_cache = {}
            
            if self.user_info["language"] == "english":
                return f"Birth information set: {birth_date}, {thai_day}"
            else:
                return f"ตั้งค่าข้อมูลวันเกิดแล้ว: {birth_date}, {thai_day}"
                
        except ValueError:
            return "Invalid birth date format. Please use YYYY-MM-DD."
        except Exception as e:
            return f"Error setting birth info: {str(e)}"
    
    def _show_history(self) -> str:
        """Show conversation history"""
        if not self.conversation_history:
            return "No conversation history yet."
        
        history_text = "=== Conversation History ===\n\n"
        for entry in self.conversation_history:
            role = "You" if entry["role"] == "user" else "Fortune Teller"
            time_str = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            history_text += f"[{time_str}] {role}: {entry['content']}\n\n"
        
        return history_text

    async def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session"""
        if not self.session_id:
            return {"error": "No active session"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_URL}/session",
                    cookies={"session_id": self.session_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": f"Failed to get session info: {str(e)}"}
    
    def save_history(self, filename: str = "fortune_chat_history.json") -> str:
        """Save conversation history to a file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            return f"Conversation history saved to {filename}"
        except Exception as e:
            return f"Error saving history: {str(e)}"
    
    def load_history(self, filename: str = "fortune_chat_history.json") -> str:
        """Load conversation history from a file"""
        try:
            if not os.path.exists(filename):
                return f"History file {filename} does not exist"
            
            with open(filename, "r", encoding="utf-8") as f:
                self.conversation_history = json.load(f)
            return f"Loaded {len(self.conversation_history)} messages from history"
        except Exception as e:
            return f"Error loading history: {str(e)}"


async def main():
    """Main function to run the chat interface"""
    print("=== Thai Fortune Teller Chat ===")
    print("Commands:")
    print("  /birth YYYY-MM-DD DAY - Set your birth date and Thai day")
    print("  /english - Switch to English responses")
    print("  /thai - Switch to Thai responses")
    print("  /history - Show conversation history")
    print("  /clear - Clear conversation history and cache")
    print("  /save - Save conversation history to file")
    print("  /load - Load conversation history from file")
    print("  /session - Show current session information")
    print("  /exit - Exit the chat")
    print("")
    
    chat = FortuneTellerChat()
    
    while True:
        user_input = input("> ")
        
        if user_input.lower() == "/exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "/save":
            result = chat.save_history()
            print(result)
            continue
        elif user_input.lower() == "/load":
            result = chat.load_history()
            print(result)
            continue
        elif user_input.lower() == "/session":
            session_info = await chat.get_session_info()
            print(json.dumps(session_info, indent=2))
            continue
        
        response = await chat.send_message(user_input)
        print("\n" + response + "\n")


if __name__ == "__main__":
    asyncio.run(main())