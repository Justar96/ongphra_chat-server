# examples/chat_history_demo.py
"""
Chat History API Demo Script

This script demonstrates how to use the chat history API endpoints, 
including sending messages, retrieving conversation history, and 
managing chat sessions.
"""

import aiohttp
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configuration
API_URL = "http://localhost:8000"

async def chat(
    prompt: str, 
    user_id: str,
    session_id: Optional[str] = None, 
    birth_date: Optional[str] = None,
    thai_day: Optional[str] = None,
    enable_fortune: bool = True
) -> Dict[str, Any]:
    """Send a chat message and get the response"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "prompt": prompt,
            "user_id": user_id,
            "enable_fortune": enable_fortune
        }
        
        if session_id:
            payload["session_id"] = session_id
            
        if birth_date:
            payload["birth_date"] = birth_date
            
        if thai_day:
            payload["thai_day"] = thai_day
        
        async with session.post(f"{API_URL}/api/chat", json=payload) as response:
            return await response.json()

async def get_sessions(user_id: str, limit: int = 10, active_only: bool = True) -> Dict[str, Any]:
    """Get user's chat sessions"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/api/chat/sessions?user_id={user_id}&limit={limit}&active_only={active_only}"
        ) as response:
            return await response.json()

async def get_history(user_id: str, session_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """Get chat history for a user or session"""
    url = f"{API_URL}/api/chat/history?user_id={user_id}&limit={limit}"
    if session_id:
        url += f"&session_id={session_id}"
        
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def end_session(session_id: str) -> Dict[str, Any]:
    """End a chat session"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/api/chat/end-session", 
            json={"session_id": session_id}
        ) as response:
            return await response.json()

async def delete_session(session_id: str) -> Dict[str, Any]:
    """Delete a chat session"""
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/api/chat/session/{session_id}") as response:
            return await response.json()

def print_json(obj: Any) -> None:
    """Pretty print a JSON object"""
    print(json.dumps(obj, indent=2, ensure_ascii=False))

async def demo():
    """Run the chat history API demo"""
    # Generate a unique user ID for this demo
    user_id = str(uuid.uuid4())
    print(f"Demo using user_id: {user_id}")
    
    # Example 1: Start a new conversation
    print("\n=== Example 1: Starting a new conversation ===")
    response = await chat("Hello, how are you today?", user_id)
    print("Chat response:")
    print_json(response)
    
    # Get the session ID from the response
    session_id = response.get("session_id")
    print(f"Session ID: {session_id}")
    
    # Example 2: Continue the conversation
    print("\n=== Example 2: Continuing the conversation ===")
    response = await chat(
        "What's the weather like?", 
        user_id, 
        session_id=session_id
    )
    print("Chat response:")
    print_json(response)
    
    # Example 3: Get user's sessions
    print("\n=== Example 3: Getting user's sessions ===")
    sessions = await get_sessions(user_id)
    print("User sessions:")
    print_json(sessions)
    
    # Example 4: Get chat history
    print("\n=== Example 4: Getting chat history ===")
    history = await get_history(user_id, session_id)
    print("Chat history:")
    print_json(history)
    
    # Example 5: Ask for a fortune reading
    print("\n=== Example 5: Adding a fortune reading to the conversation ===")
    birth_date = "1990-01-01"
    thai_day = "จันทร์"
    response = await chat(
        "Can you tell me about my fortune?", 
        user_id, 
        session_id=session_id,
        birth_date=birth_date,
        thai_day=thai_day
    )
    print("Fortune response:")
    print_json(response)
    
    # Example 6: Get updated history with fortune
    print("\n=== Example 6: Getting updated chat history with fortune ===")
    history = await get_history(user_id, session_id)
    print("Updated chat history:")
    print_json(history)
    
    # Example 7: End the session
    print("\n=== Example 7: Ending the chat session ===")
    end_result = await end_session(session_id)
    print("End session result:")
    print_json(end_result)
    
    # Example 8: Starting a new session
    print("\n=== Example 8: Starting a new session ===")
    response = await chat("Let's start a new conversation", user_id)
    new_session_id = response.get("session_id")
    print(f"New session ID: {new_session_id}")
    print("Chat response:")
    print_json(response)
    
    # Example 9: Get all sessions for a user
    print("\n=== Example 9: Getting all sessions including inactive ===")
    all_sessions = await get_sessions(user_id, active_only=False)
    print("All user sessions:")
    print_json(all_sessions)
    
    # Example 10: Delete the first session
    print("\n=== Example 10: Deleting a chat session ===")
    delete_result = await delete_session(session_id)
    print("Delete session result:")
    print_json(delete_result)
    
    print("\n=== Demo completed! ===")

if __name__ == "__main__":
    asyncio.run(demo()) 