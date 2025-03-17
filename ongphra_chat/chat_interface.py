#!/usr/bin/env python
# chat_interface.py
import asyncio
import sys
import os
import logging
import argparse
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import SSE for streaming responses
try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    logger = logging.getLogger("chat_interface")
    logger.warning("sse-starlette not found. Installing it...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sse-starlette>=1.6.5"])
    from sse_starlette.sse import EventSourceResponse

# Add the parent directory to sys.path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.core.service import FortuneService
from app.services.calculator import CalculatorService
from app.services.meaning import MeaningService
from app.services.prompt import PromptService
from app.services.response import ResponseService
from app.repository.category_repository import CategoryRepository
from app.repository.reading_repository import ReadingRepository
from app.config.database import DatabaseManager
from app.config.settings import get_settings


# Configure basic console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("chat_interface")

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database connection pool
    try:
        await DatabaseManager.initialize_pool()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {str(e)}", exc_info=True)
    
    yield
    
    # Shutdown: Close database connection pool
    try:
        await DatabaseManager.close_pool()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database connection pool: {str(e)}", exc_info=True)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Fortune Telling Chat Interface",
    lifespan=lifespan
)

# Create templates directory if it doesn't exist
templates_dir = os.path.join(current_dir, "templates")
os.makedirs(templates_dir, exist_ok=True)

# Create templates instance
templates = Jinja2Templates(directory=templates_dir)

# Create static directory if it doesn't exist
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create CSS file
css_file_path = os.path.join(static_dir, "css", "style.css")
if not os.path.exists(css_file_path):
    with open(css_file_path, "w", encoding="utf-8") as f:
        f.write("""
        body {
            font-family: 'Kanit', 'Sarabun', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 70vh;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background-color: white;
        }
        .chat-header {
            background-color: #4a148c;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 1.2em;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            max-width: 80%;
        }
        .user-message {
            background-color: #e1f5fe;
            align-self: flex-end;
            margin-left: auto;
        }
        .bot-message {
            background-color: #f5f5f5;
            align-self: flex-start;
        }
        .chat-input {
            display: flex;
            padding: 10px;
            border-top: 1px solid #ddd;
            background-color: #f9f9f9;
        }
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 10px;
        }
        .chat-input button {
            padding: 10px 15px;
            background-color: #4a148c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .chat-input button:hover {
            background-color: #7b1fa2;
        }
        .user-info {
            margin-bottom: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .user-info h2 {
            margin-top: 0;
            color: #4a148c;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .btn {
            padding: 10px 15px;
            background-color: #4a148c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn:hover {
            background-color: #7b1fa2;
        }
        .streaming {
            font-style: italic;
            color: #666;
        }
        """)

# Create JavaScript file
js_file_path = os.path.join(static_dir, "js", "chat.js")
if not os.path.exists(js_file_path):
    with open(js_file_path, "w", encoding="utf-8") as f:
        f.write("""
        let socket;
        let isConnected = false;
        
        function connectWebSocket() {
            // Get user info
            const birthDate = document.getElementById('birth-date').value;
            const thaiDay = document.getElementById('thai-day').value;
            const language = document.getElementById('language').value;
            const streamMode = document.getElementById('stream-mode').checked;
            
            if (!birthDate || !thaiDay) {
                alert('Please enter birth date and Thai day');
                return;
            }
            
            // Create WebSocket connection
            socket = new WebSocket(`ws://${window.location.host}/ws/${birthDate}/${thaiDay}/${language}/${streamMode}`);
            
            socket.onopen = function(e) {
                console.log('WebSocket connection established');
                isConnected = true;
                document.getElementById('status-indicator').textContent = 'Connected';
                document.getElementById('status-indicator').style.color = 'green';
                document.getElementById('connect-btn').disabled = true;
                document.getElementById('disconnect-btn').disabled = false;
                document.getElementById('message-input').disabled = false;
                document.getElementById('send-btn').disabled = false;
                
                // Add system message
                addMessage('System', 'Connected to fortune telling service. You can now ask questions.', 'bot-message');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'stream') {
                    // Handle streaming response
                    const messageElement = document.querySelector('.message.streaming');
                    if (messageElement) {
                        messageElement.textContent += data.content;
                    } else {
                        addMessage('Fortune Teller', data.content, 'bot-message streaming');
                    }
                } else if (data.type === 'complete') {
                    // Handle complete message
                    const streamingElement = document.querySelector('.message.streaming');
                    if (streamingElement) {
                        streamingElement.classList.remove('streaming');
                    } else {
                        addMessage('Fortune Teller', data.content, 'bot-message');
                    }
                } else {
                    // Handle regular message
                    addMessage('Fortune Teller', data.content, 'bot-message');
                }
            };
            
            socket.onclose = function(event) {
                console.log('WebSocket connection closed');
                isConnected = false;
                document.getElementById('status-indicator').textContent = 'Disconnected';
                document.getElementById('status-indicator').style.color = 'red';
                document.getElementById('connect-btn').disabled = false;
                document.getElementById('disconnect-btn').disabled = true;
                document.getElementById('message-input').disabled = true;
                document.getElementById('send-btn').disabled = true;
                
                // Add system message
                addMessage('System', 'Disconnected from fortune telling service.', 'bot-message');
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                addMessage('System', 'Error connecting to fortune telling service.', 'bot-message');
            };
        }
        
        function disconnectWebSocket() {
            if (socket && isConnected) {
                socket.close();
            }
        }
        
        function sendMessage() {
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (message && isConnected) {
                // Add user message to chat
                addMessage('You', message, 'user-message');
                
                // Send message to server
                socket.send(JSON.stringify({ question: message }));
                
                // Clear input
                messageInput.value = '';
            }
        }
        
        function addMessage(sender, content, className) {
            const chatMessages = document.querySelector('.chat-messages');
            const messageElement = document.createElement('div');
            messageElement.className = `message ${className}`;
            
            const senderElement = document.createElement('div');
            senderElement.className = 'message-sender';
            senderElement.textContent = sender;
            
            const contentElement = document.createElement('div');
            contentElement.className = 'message-content';
            contentElement.textContent = content;
            
            messageElement.appendChild(senderElement);
            messageElement.appendChild(contentElement);
            
            chatMessages.appendChild(messageElement);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('connect-btn').addEventListener('click', connectWebSocket);
            document.getElementById('disconnect-btn').addEventListener('click', disconnectWebSocket);
            document.getElementById('send-btn').addEventListener('click', sendMessage);
            
            // Send message on Enter key
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        });
        """)

# Create HTML template
template_file_path = os.path.join(templates_dir, "chat.html")
if not os.path.exists(template_file_path):
    with open(template_file_path, "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Fortune Telling Chat Interface</title>
            <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&family=Sarabun:wght@300;400;500&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <div class="container">
                <h1>Thai Fortune Telling Chat Interface</h1>
                
                <div class="user-info">
                    <h2>User Information</h2>
                    <div class="form-group">
                        <label for="birth-date">Birth Date:</label>
                        <input type="date" id="birth-date" name="birth-date" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="thai-day">Thai Day:</label>
                        <select id="thai-day" name="thai-day" required>
                            <option value="">Select Thai Day</option>
                            <option value="อาทิตย์">อาทิตย์ (Sunday)</option>
                            <option value="จันทร์">จันทร์ (Monday)</option>
                            <option value="อังคาร">อังคาร (Tuesday)</option>
                            <option value="พุธ">พุธ (Wednesday)</option>
                            <option value="พฤหัสบดี">พฤหัสบดี (Thursday)</option>
                            <option value="ศุกร์">ศุกร์ (Friday)</option>
                            <option value="เสาร์">เสาร์ (Saturday)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="language">Language:</label>
                        <select id="language" name="language">
                            <option value="thai">Thai</option>
                            <option value="english">English</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="stream-mode">
                            <input type="checkbox" id="stream-mode" name="stream-mode" checked>
                            Enable Streaming Mode
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <button id="connect-btn" class="btn">Connect</button>
                        <button id="disconnect-btn" class="btn" disabled>Disconnect</button>
                        <span>Status: <span id="status-indicator" style="color: red;">Disconnected</span></span>
                    </div>
                </div>
                
                <div class="chat-container">
                    <div class="chat-header">
                        Fortune Telling Chat
                    </div>
                    <div class="chat-messages">
                        <div class="message bot-message">
                            <div class="message-sender">System</div>
                            <div class="message-content">Welcome to the Fortune Telling Chat Interface. Please connect to start a session.</div>
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="message-input" placeholder="Type your question here..." disabled>
                        <button id="send-btn" disabled>Send</button>
                    </div>
                </div>
            </div>
            
            <script src="/static/js/chat.js"></script>
        </body>
        </html>
        """)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, message: str, client_id: str, message_type: str = "message"):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": message_type,
                "content": message
            })


# Initialize connection manager
manager = ConnectionManager()


# Dependency to get FortuneService
async def get_fortune_service() -> FortuneService:
    """Dependency for getting the FortuneService instance"""
    settings = get_settings()
    
    # Initialize repositories
    category_repository = CategoryRepository()
    reading_repository = ReadingRepository()
    
    # Initialize services
    calculator_service = CalculatorService()
    meaning_service = MeaningService(category_repository, reading_repository)
    prompt_service = PromptService()
    response_service = ResponseService()
    
    # Create and return FortuneService
    return FortuneService(
        calculator_service,
        meaning_service,
        prompt_service,
        response_service
    )


# Routes
@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Render the chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.websocket("/ws/{birth_date}/{thai_day}/{language}/{stream}")
async def websocket_endpoint(
    websocket: WebSocket,
    birth_date: str,
    thai_day: str,
    language: str,
    stream: bool,
):
    """WebSocket endpoint for chat"""
    # Generate client ID
    client_id = f"{birth_date}_{thai_day}_{datetime.now().timestamp()}"
    
    # Connect to WebSocket
    await manager.connect(websocket, client_id)
    
    try:
        # Initialize fortune service
        fortune_service = await get_fortune_service()
        
        # Parse birth date
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            await manager.send_message(
                "Invalid birth date format. Please use YYYY-MM-DD format.",
                client_id
            )
            return
        
        # Send welcome message
        await manager.send_message(
            f"Connected to fortune telling service. Birth date: {birth_date}, Thai day: {thai_day}, Language: {language}",
            client_id
        )
        
        # Process messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                data_json = json.loads(data)
                question = data_json.get("question", "")
            except json.JSONDecodeError:
                await manager.send_message("Invalid message format. Please send a valid JSON object.", client_id)
                continue
            
            if not question:
                await manager.send_message("Please provide a question.", client_id)
                continue
            
            try:
                # Process question
                if stream:
                    # Handle streaming response
                    response_generator = await fortune_service.get_fortune(
                        birth_date_obj,
                        thai_day,
                        question,
                        language,
                        client_id,
                        stream=True
                    )
                    
                    # Stream the response chunks
                    async for chunk in response_generator:
                        await manager.send_message(chunk, client_id, "stream")
                    
                    # Send completion message
                    await manager.send_message("", client_id, "complete")
                else:
                    # Handle standard response
                    response = await fortune_service.get_fortune(
                        birth_date_obj,
                        thai_day,
                        question,
                        language,
                        client_id,
                        stream=False
                    )
                    
                    await manager.send_message(response.fortune, client_id)
            
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}", exc_info=True)
                await manager.send_message(f"Error: {str(e)}", client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        manager.disconnect(client_id)


@app.post("/general-question")
async def general_question(
    request: Request,
    question: str = Form(...),
    language: str = Form("thai"),
    stream: bool = Form(False)
):
    """Handle general questions without birth information"""
    try:
        # Initialize fortune service
        fortune_service = await get_fortune_service()
        
        # Generate client ID
        client_id = f"general_{datetime.now().timestamp()}"
        
        # Get response
        if stream:
            # For streaming responses, we need to use Server-Sent Events
            async def event_generator():
                response_generator = await fortune_service.get_general_response(
                    question=question,
                    language=language,
                    user_id=client_id,
                    stream=True
                )
                
                yield {"event": "start", "data": json.dumps({"type": "start"})}
                
                # The response_generator is now directly an async generator
                async for chunk in response_generator:
                    yield {"event": "message", "data": json.dumps({"type": "chunk", "content": chunk})}
                
                yield {"event": "end", "data": json.dumps({"type": "end"})}
            
            return EventSourceResponse(event_generator())
        else:
            # For standard responses, return JSON
            response = await fortune_service.get_general_response(
                question=question,
                language=language,
                user_id=client_id,
                stream=False
            )
            
            return JSONResponse(content={"fortune": response})
    
    except Exception as e:
        logger.error(f"Error processing general question: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/general-question")
async def general_question_get(
    request: Request,
    question: str,
    language: str = "thai",
    stream: bool = True
):
    """Handle general questions without birth information (GET method for EventSource)"""
    try:
        # Initialize fortune service
        fortune_service = await get_fortune_service()
        
        # Generate client ID
        client_id = f"general_{datetime.now().timestamp()}"
        
        # For GET requests, we always use streaming
        async def event_generator():
            response_generator = await fortune_service.get_general_response(
                question=question,
                language=language,
                user_id=client_id,
                stream=True
            )
            
            yield {"event": "start", "data": json.dumps({"type": "start"})}
            
            # The response_generator is now directly an async generator
            async for chunk in response_generator:
                yield {"event": "message", "data": json.dumps({"type": "chunk", "content": chunk})}
            
            yield {"event": "end", "data": json.dumps({"type": "end"})}
        
        return EventSourceResponse(event_generator())
    
    except Exception as e:
        logger.error(f"Error processing general question: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fortune Telling Chat Interface")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set debug level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Run the application
    uvicorn.run(
        "chat_interface:app",
        host=args.host,
        port=args.port,
        reload=args.debug
    ) 