# examples/chat_interface.py
import asyncio
import json
import httpx
import os
from datetime import datetime
from typing import Dict, Optional

API_URL = "http://localhost:8000/fortune"

class FortuneTellerChat:
    """Simple chat interface for the Thai Fortune Teller API"""
    
    def __init__(self):
        self.user_info = {
            "birth_date": None,
            "thai_day": None,
            "language": "thai"
        }
    
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
            
            # Send request to API
            try:
                print(f"Sending request to {API_URL} with payload: {payload}")
                response = await client.post(API_URL, json=payload)
                response.raise_for_status()
                data = response.json()
                print(f"Received response: {data}")
                return data["fortune"]
            except httpx.HTTPStatusError as e:
                error_detail = "Unknown error"
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get('detail', str(e))
                except Exception:
                    error_detail = f"Status code: {e.response.status_code}, Response: {e.response.text}"
                return f"Error: {error_detail}"
            except Exception as e:
                return f"An error occurred: {str(e)}"
    
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
            
            if self.user_info["language"] == "english":
                return f"Birth information set: {birth_date}, {thai_day}"
            else:
                return f"ตั้งค่าข้อมูลวันเกิดแล้ว: {birth_date}, {thai_day}"
                
        except ValueError:
            return "Invalid birth date format. Please use YYYY-MM-DD."
        except Exception as e:
            return f"Error setting birth info: {str(e)}"


async def main():
    """Main function to run the chat interface"""
    print("=== Thai Fortune Teller Chat ===")
    print("Commands:")
    print("  /birth YYYY-MM-DD DAY - Set your birth date and Thai day")
    print("  /english - Switch to English responses")
    print("  /thai - Switch to Thai responses")
    print("  /exit - Exit the chat")
    print("")
    
    chat = FortuneTellerChat()
    
    while True:
        user_input = input("> ")
        
        if user_input.lower() == "/exit":
            print("Goodbye!")
            break
        
        response = await chat.send_message(user_input)
        print("\n" + response + "\n")


if __name__ == "__main__":
    asyncio.run(main())