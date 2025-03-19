# Ongphra Chat API

A FastAPI backend service for fortune telling and chat with context memory.

## Overview

This API provides endpoints for:
- Fortune telling based on birth date and Thai day
- Chat interactions with context memory
- Streaming chat responses
- Birth chart analysis
- **NEW**: Integrated AI fortune reading system
- **NEW**: Persistent chat history storage

## Features

### Integrated AI Fortune System

The platform now features an AI-powered fortune reading system that:
- Automatically detects when users ask for fortune readings
- Extracts birth date information from messages
- Remembers birth information across conversations
- Provides contextual fortune readings based on the user's question

For more details, see the [AI Fortune Integration Guide](docs/ai_fortune_integration.md).

### Chat History System

The API now includes a persistent chat history system that:
- Stores all chat messages in a database for future reference
- Organizes conversations into sessions for better context management
- Provides endpoints to retrieve past conversations
- Tracks fortune readings separately for analysis
- Supports session management (creating, ending, and deleting sessions)

For more details, see the [Chat History Guide](docs/chat_history.md).

### Endpoint Design

The API is designed with a unified approach to fortune processing:

1. **Chat Endpoints** (`/api/chat` and `/api/chat/stream`)
   - Handle both regular conversation and fortune readings
   - Automatically detect fortune requests using keyword analysis
   - Can extract birth dates directly from user messages
   - Support the `enable_fortune` parameter to control fortune detection
   - **New**: Now save all messages to the database for future reference

2. **Fortune Endpoint** (`/api/fortune`)
   - Dedicated endpoint for direct fortune readings
   - Requires birth date to be explicitly provided
   - Uses the same underlying fortune engine as the chat endpoints
   - Ideal for applications focused specifically on fortune readings

3. **Birth Chart Endpoint** (`/api/birth-chart/enriched`)
   - Advanced endpoint for detailed astrological information
   - Returns comprehensive birth chart data with meanings

4. **NEW: Chat History Endpoints** (`/api/chat/...`)
   - `/api/chat/sessions` - Get a list of user's chat sessions
   - `/api/chat/history` - Get conversation history for a session
   - `/api/chat/end-session` - Mark a session as inactive
   - `/api/chat/session/{session_id}` - Delete a specific session

All endpoints share the same session management system, ensuring user birth information and context are preserved across different API calls and sessions.

## API Documentation

The API documentation is available at:
- Development: http://localhost:8000/docs
- Production: http://localhost:8000/docs (or your production host)

## Requirements

- Python 3.9+
- See `requirements.txt` for all dependencies

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the API

### Development Mode

```
python start_dev_server.py
```

Or use the batch file:
```
start_dev_server.bat
```

### Production Mode

```
python start_server.py
```

Or use the batch file:
```
start_server.bat
```

## Environment Variables

The following environment variables can be configured in a `.env` file:

- `HOST`: Host to bind the server to (default: "0.0.0.0")
- `PORT`: Port to run the server on (default: 8000)
- `LOG_LEVEL`: Logging level (default: "DEBUG" for development, "INFO" for production)
- `DEBUG`: Enable debug mode (default: "true" for development, "false" for production)

## Frontend Integration

This API is designed to work with any frontend application. Follow these instructions to integrate your frontend with the Ongphra Chat API.

### API Base URL

- Development: `http://localhost:8000`
- Production: Your production server URL

### CORS Configuration

The API is configured to accept requests from all origins (`*`) by default. If you need to restrict this to specific domains, modify the `CORS_ORIGINS` environment variable in the `.env` file.

### Authentication and Session Management

The API uses a user_id parameter for session tracking. Here's how to properly implement session management:

```javascript
// Session management utilities
const OngphraSession = {
  // Key for localStorage
  USER_ID_KEY: 'ongphra_user_id',
  
  // Get existing user ID or create a new one
  getUserId: function() {
    let userId = localStorage.getItem(this.USER_ID_KEY);
    
    if (!userId) {
      // Generate UUID v4
      userId = crypto.randomUUID ? crypto.randomUUID() : 
               ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
                 (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
               );
      localStorage.setItem(this.USER_ID_KEY, userId);
    }
    
    return userId;
  },
  
  // Save user birth information
  saveBirthInfo: function(birthDate, thaiDay) {
    localStorage.setItem('ongphra_birth_date', birthDate);
    localStorage.setItem('ongphra_thai_day', thaiDay);
  },
  
  // Get stored birth information
  getBirthInfo: function() {
    return {
      birthDate: localStorage.getItem('ongphra_birth_date'),
      thaiDay: localStorage.getItem('ongphra_thai_day')
    };
  },
  
  // Clear user session on server and locally
  clearSession: async function() {
    const userId = this.getUserId();
    
    if (userId) {
      try {
        // Clear on server
        await fetch(`http://localhost:8000/api/session/${userId}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.error('Error clearing server session:', error);
      }
      
      // Clear locally
      localStorage.removeItem(this.USER_ID_KEY);
      localStorage.removeItem('ongphra_birth_date');
      localStorage.removeItem('ongphra_thai_day');
    }
  }
};
```

### API Client Implementation

Here's a complete API client implementation that handles all endpoints:

```javascript
class OngphraAPI {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.userId = OngphraSession.getUserId();
  }
  
  // Helper method for API calls
  async apiCall(endpoint, method = 'GET', body = null) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      }
    };
    
    if (body) {
      options.body = JSON.stringify(body);
    }
    
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error: ${response.status}`);
      }
      
      return method === 'DELETE' ? { success: true } : await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }
  
  // Get fortune reading
  async getFortune(question, language = 'thai') {
    const birthInfo = OngphraSession.getBirthInfo();
    
    if (!birthInfo.birthDate || !birthInfo.thaiDay) {
      throw new Error('Birth information is required for fortune telling');
    }
    
    return this.apiCall('/api/fortune', 'POST', {
      birth_date: birthInfo.birthDate,
      thai_day: birthInfo.thaiDay,
      question,
      language,
      user_id: this.userId
    });
  }
  
  // Send chat message
  async sendChatMessage(prompt, language = 'thai') {
    const birthInfo = OngphraSession.getBirthInfo();
    
    // Include birth info if available, but not required
    const payload = {
      prompt,
      language,
      user_id: this.userId
    };
    
    if (birthInfo.birthDate) payload.birth_date = birthInfo.birthDate;
    if (birthInfo.thaiDay) payload.thai_day = birthInfo.thaiDay;
    
    return this.apiCall('/api/chat', 'POST', payload);
  }
  
  // Get birth chart
  async getBirthChart(question) {
    const birthInfo = OngphraSession.getBirthInfo();
    
    if (!birthInfo.birthDate || !birthInfo.thaiDay) {
      throw new Error('Birth information is required for birth chart');
    }
    
    return this.apiCall('/api/birth-chart/enriched', 'POST', {
      birth_date: birthInfo.birthDate,
      thai_day: birthInfo.thaiDay,
      question,
      user_id: this.userId
    });
  }
  
  // Get user context
  async getUserContext() {
    return this.apiCall(`/api/session/${this.userId}/context`);
  }
  
  // Clear user session
  async clearSession() {
    return this.apiCall(`/api/session/${this.userId}`, 'DELETE');
  }
  
  // Stream chat response
  streamChatResponse(prompt, language = 'thai', callbacks = {}) {
    const birthInfo = OngphraSession.getBirthInfo();
    
    // Include birth info if available, but not required
    const payload = {
      prompt,
      language,
      user_id: this.userId
    };
    
    if (birthInfo.birthDate) payload.birth_date = birthInfo.birthDate;
    if (birthInfo.thaiDay) payload.thai_day = birthInfo.thaiDay;
    
    // Create URL with searchParams for better compatibility
    const url = new URL(`${this.baseUrl}/api/chat/stream`);
    
    // Set up event source
    const eventSource = new EventSource(url.toString());
    
    // Post the request data
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    }).catch(error => {
      if (callbacks.onError) callbacks.onError(error);
      eventSource.close();
    });
    
    // Set up event handlers
    let fullText = '';
    
    eventSource.onmessage = (event) => {
      try {
        const chunk = event.data;
        if (chunk) {
          fullText += chunk;
          if (callbacks.onChunk) callbacks.onChunk(chunk, fullText);
        }
      } catch (error) {
        if (callbacks.onError) callbacks.onError(error);
      }
    };
    
    eventSource.onerror = (error) => {
      if (callbacks.onError) callbacks.onError(error);
      eventSource.close();
    };
    
    eventSource.addEventListener('end', () => {
      if (callbacks.onComplete) callbacks.onComplete(fullText);
      eventSource.close();
    });
    
    // Return control methods
    return {
      cancel: () => {
        eventSource.close();
        if (callbacks.onCancel) callbacks.onCancel();
      }
    };
  }
}
```

### Usage Examples

#### 1. Initial Setup and User Onboarding

```javascript
// Initialize the API client
const api = new OngphraAPI('http://localhost:8000');

// Save user birth information (only needed once)
function saveBirthInfo() {
  const birthDate = document.getElementById('birth-date').value;
  const thaiDay = document.getElementById('thai-day').value;
  
  if (!birthDate || !thaiDay) {
    alert('Please enter both birth date and Thai day');
    return;
  }
  
  // Save to session manager
  OngphraSession.saveBirthInfo(birthDate, thaiDay);
  
  alert('Birth information saved successfully!');
}
```

#### 2. Regular Chat Interaction

```javascript
// Send a chat message
async function sendChatMessage() {
  const messageInput = document.getElementById('message-input');
  const prompt = messageInput.value.trim();
  
  if (!prompt) return;
  
  try {
    // Display user message in UI
    displayMessage('user', prompt);
    
    // Clear input
    messageInput.value = '';
    
    // Send to API
    const response = await api.sendChatMessage(prompt);
    
    // Display response in UI
    displayMessage('bot', response.text);
  } catch (error) {
    console.error('Chat error:', error);
    displayMessage('error', 'Sorry, there was an error sending your message.');
  }
}

// Helper function to display messages in UI
function displayMessage(type, content) {
  const chatContainer = document.getElementById('chat-container');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}-message`;
  messageDiv.textContent = content;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}
```

#### 3. Streaming Chat Implementation

```javascript
// Send a streaming chat message
function sendStreamingChatMessage() {
  const messageInput = document.getElementById('message-input');
  const prompt = messageInput.value.trim();
  
  if (!prompt) return;
  
  // Display user message in UI
  displayMessage('user', prompt);
  
  // Clear input
  messageInput.value = '';
  
  // Create a placeholder for the streaming response
  const chatContainer = document.getElementById('chat-container');
  const responsePlaceholder = document.createElement('div');
  responsePlaceholder.className = 'message bot-message streaming';
  responsePlaceholder.id = `response-${Date.now()}`;
  chatContainer.appendChild(responsePlaceholder);
  
  // Stream the response
  const streamController = api.streamChatResponse(prompt, 'thai', {
    onChunk: (chunk, fullText) => {
      // Update the placeholder with each chunk
      responsePlaceholder.textContent = fullText;
      chatContainer.scrollTop = chatContainer.scrollHeight;
    },
    onComplete: (fullText) => {
      // Remove streaming class when complete
      responsePlaceholder.classList.remove('streaming');
    },
    onError: (error) => {
      console.error('Stream error:', error);
      responsePlaceholder.classList.remove('streaming');
      responsePlaceholder.classList.add('error');
      responsePlaceholder.textContent = 'Sorry, there was an error receiving the response.';
    }
  });
  
  // Optional: Add a cancel button
  const cancelButton = document.createElement('button');
  cancelButton.textContent = 'Cancel';
  cancelButton.onclick = () => {
    streamController.cancel();
    responsePlaceholder.classList.remove('streaming');
    responsePlaceholder.classList.add('cancelled');
    responsePlaceholder.textContent += ' [cancelled]';
  };
  chatContainer.appendChild(cancelButton);
}
```

#### 4. Fortune Telling

```javascript
// Get a fortune reading
async function getFortune() {
  const questionInput = document.getElementById('fortune-question');
  const question = questionInput.value.trim();
  
  if (!question) {
    alert('Please enter a question');
    return;
  }
  
  try {
    // Show loading indicator
    document.getElementById('fortune-result').textContent = 'Loading...';
    
    // Get fortune from API
    const response = await api.getFortune(question);
    
    // Display result
    document.getElementById('fortune-result').textContent = response.reading.meaning;
  } catch (error) {
    console.error('Fortune error:', error);
    document.getElementById('fortune-result').textContent = 
      'Error: ' + (error.message || 'Could not get fortune reading');
  }
}
```

### Handling Birth Information

Always check if birth information is available before making requests that require it:

```javascript
// Check if birth info is needed
function checkBirthInfo() {
  const birthInfo = OngphraSession.getBirthInfo();
  
  if (!birthInfo.birthDate || !birthInfo.thaiDay) {
    // Show birth info form
    document.getElementById('birth-info-form').style.display = 'block';
    return false;
  }
  
  return true;
}

// Before making a request that requires birth info
function getPersonalizedFortune() {
  if (!checkBirthInfo()) {
    alert('Please enter your birth information first');
    return;
  }
  
  // Proceed with API call
  getFortune();
}
```

### CSS for Streaming Messages

Add these styles to create a nice streaming effect:

```css
.message {
  padding: 10px;
  margin: 5px 0;
  border-radius: 8px;
}

.user-message {
  background-color: #e1f5fe;
  align-self: flex-end;
}

.bot-message {
  background-color: #f1f1f1;
  align-self: flex-start;
}

.bot-message.streaming {
  position: relative;
}

.bot-message.streaming:after {
  content: "";
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  margin-left: 5px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}
```

### Error Handling

Add comprehensive error handling to improve user experience:

```javascript
// Global error handler
window.addEventListener('unhandledrejection', function(event) {
  console.error('Unhandled Promise Rejection:', event.reason);
  
  // Show user-friendly error message
  const errorMessage = event.reason.message || 'An unexpected error occurred';
  alert(`Error: ${errorMessage}`);
});

// Network status monitoring
window.addEventListener('online', () => {
  console.log('Connection restored');
  document.getElementById('connection-status').textContent = 'Online';
  document.getElementById('connection-status').className = 'status-online';
});

window.addEventListener('offline', () => {
  console.log('Connection lost');
  document.getElementById('connection-status').textContent = 'Offline';
  document.getElementById('connection-status').className = 'status-offline';
});
```

## API Endpoints

### Fortune Telling

```
POST /api/fortune
```
Request body:
```json
{
  "birth_date": "YYYY-MM-DD",
  "thai_day": "อาทิตย์",
  "question": "Will I be lucky in love?",
  "language": "thai"
}
```

### Chat

```
POST /api/chat
```
Request body:
```json
{
  "prompt": "Tell me about my career prospects",
  "birth_date": "YYYY-MM-DD",
  "thai_day": "อาทิตย์",
  "language": "thai",
  "user_id": "optional-user-id"
}
```

### Streaming Chat

```
POST /api/chat/stream
```
Request body:
```json
{
  "prompt": "Tell me about my career prospects",
  "birth_date": "YYYY-MM-DD",
  "thai_day": "อาทิตย์",
  "language": "thai",
  "user_id": "optional-user-id"
}
```

### Session Management

```
DELETE /api/session/{user_id}
```

```
GET /api/session/{user_id}/context
```

### Birth Chart

```
POST /api/birth-chart/enriched
```
Request body:
```json
{
  "birth_date": "YYYY-MM-DD",
  "thai_day": "อาทิตย์",
  "question": "What does my birth chart say about my future?",
  "user_id": "optional-user-id"
}
```

### NEW: Chat History

```
GET /api/chat/sessions?user_id={user_id}
```

```
GET /api/chat/history?user_id={user_id}&session_id={session_id}
```

```
POST /api/chat/end-session
```
Request body:
```json
{
  "session_id": "session-uuid"
}
```

```
DELETE /api/chat/session/{session_id}
```

## Database Migration

To set up the chat history database tables, run the migration script:

```
# Windows PowerShell
.\run_migration.ps1

# Linux/Mac
python -m app.db.migrate
```

## Error Handling

The API returns standard HTTP status codes and error responses:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found
- 500: Internal Server Error

Error response format:
```json
{
  "detail": "Error message"
}
```

## Logging

Logs are stored in the `logs` directory:
- `app.log`: General application logs
- `csv_operations.log`: CSV-specific operations
