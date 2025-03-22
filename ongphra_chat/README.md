# Thai Fortune API - Frontend Developer Guide

This document provides a comprehensive guide for frontend developers on how to interact with the Thai Fortune API. The API supports chat conversations with an AI assistant proficient in Thai language and Thai fortune telling using the 7N9B system.

## API Base URL

```
https://your-api-base-url.com/api/v1
```

## Authentication

Currently, the API uses simple identification with `user_id` parameters rather than formal authentication. Ensure you provide a consistent user ID for tracking conversations.

## Chat API Endpoints

### Create or Continue a Chat Session

#### `POST /chat/message`

Send a single message to the chatbot and get a response.

**Request Body:**
```json
{
  "message": "สวัสดี คุณสบายดีไหม?",
  "user_id": "user-123",
  "session_id": "optional-session-id",
  "stream": false
}
```

**Parameters:**
- `message`: The user's message (required)
- `user_id`: Unique identifier for the user (optional, will be generated if not provided)
- `session_id`: Identifier for the conversation session (optional, will be generated if not provided)
- `stream`: Whether to stream the response (default: false)

**Response:**
```json
{
  "status": {
    "success": true
  },
  "message_id": "msg-uuid",
  "user_id": "user-123",
  "session_id": "session-456",
  "response": {
    "id": "chatcmpl-123",
    "created": 1677858242,
    "model": "gpt-4o-mini",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "สวัสดีค่ะ ดิฉันสบายดี ขอบคุณที่ถาม คุณล่ะคะ เป็นอย่างไรบ้าง?"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 12,
      "completion_tokens": 28,
      "total_tokens": 40
    }
  },
  "timestamp": 1677858242
}
```

### Stream a Chat Message

#### `POST /chat/stream`

Send a message and receive streaming responses using POST method.

**Request Body:**
```json
{
  "message": "คุณช่วยอธิบายเลข 7 ฐาน 9 ให้หน่อยได้ไหม",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

**Response:**
Server-sent events (SSE) with content-type `text/event-stream`. Each chunk will contain:

```
data: {"status":"streaming","message_id":"msg-uuid","user_id":"user-123","session_id":"session-456","content":"สวัสดี"}

data: {"status":"streaming","message_id":"msg-uuid","user_id":"user-123","session_id":"session-456","content":"ค่ะ"}

data: {"status":"complete","message_id":"msg-uuid","user_id":"user-123","session_id":"session-456","content":"","complete_response":"สวัสดีค่ะ ดิฉันสบายดี ขอบคุณที่ถาม คุณล่ะคะ เป็นอย่างไรบ้าง?"}
```

#### `GET /chat/stream` (EventSource Support)

Stream chat responses using GET method for better compatibility with EventSource/SSE.

**Query Parameters:**
- `message`: The user's message (required)
- `user_id`: User identifier (optional)
- `session_id`: Session identifier (optional)

**Example URL:**
```
GET /api/v1/chat/stream?message=สวัสดี&user_id=user-123&session_id=session-456
```

**Response:**
Server-sent events with the same format as the POST endpoint. This is the recommended method for browser-based EventSource implementations.

**Example JavaScript usage:**
```javascript
// Using native EventSource
const params = new URLSearchParams({
  message: "สวัสดี คุณสบายดีไหม?",
  user_id: "user-123",
  session_id: "session-456"
});

const eventSource = new EventSource(`/api/v1/chat/stream?${params.toString()}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  
  if (data.status === "complete") {
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error("EventSource error:", error);
  eventSource.close();
};
```

### Check WebSocket Availability

#### `GET /chat/ws-available`

Check if the WebSocket chat endpoint is available.

**Response:**
```json
{
  "status": {
    "success": true
  },
  "available": true,
  "websocket_url": "/api/v1/ws/chat"
}
```

### WebSocket Chat Connection

#### `WebSocket /api/v1/ws/chat`

Connect to the WebSocket endpoint to receive real-time streaming responses.

**Connection Process:**
1. Connect to the WebSocket endpoint
2. Send initial connection parameters as JSON
3. Exchange messages

**Initial Connection Message:**
```json
{
  "user_id": "user-123",
  "session_id": "session-456"
}
```

**Send Message:**
```json
{
  "message": "สวัสดี คุณสบายดีไหม?"
}
```

**Receive Messages:**

1. Connection Confirmation:
```json
{
  "event": "connected",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

2. Message Received Confirmation:
```json
{
  "event": "message_received",
  "message_id": "msg-uuid",
  "user_id": "user-123"
}
```

3. Content Chunks:
```json
{
  "event": "chunk",
  "message_id": "msg-uuid",
  "content": "สวัสดี",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

4. Completion:
```json
{
  "event": "complete",
  "message_id": "msg-uuid",
  "content": "สวัสดีค่ะ ดิฉันสบายดี ขอบคุณที่ถาม คุณล่ะคะ เป็นอย่างไรบ้าง?",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

5. Error (if applicable):
```json
{
  "event": "error",
  "message_id": "msg-uuid",
  "error": "Error message",
  "user_id": "user-123",
  "session_id": "session-456"
}
```

### Get Chat Sessions

#### `GET /chat/sessions?user_id=user-123`

Get all chat sessions for a user.

**Query Parameters:**
- `user_id`: The user's identifier (required)

**Response:**
```json
{
  "status": {
    "success": true
  },
  "sessions": [
    {
      "id": "session-456",
      "user_id": "user-123",
      "title": "Chat 2023-03-21 09:45",
      "created_at": "2023-03-21T09:45:32.123Z",
      "updated_at": "2023-03-21T10:15:44.567Z",
      "is_active": true
    },
    {
      "id": "session-789",
      "user_id": "user-123",
      "title": "Chat 2023-03-20 14:30",
      "created_at": "2023-03-20T14:30:15.890Z",
      "updated_at": "2023-03-20T14:45:22.345Z",
      "is_active": false
    }
  ],
  "count": 2
}
```

### Get Chat History

#### `GET /chat/history?session_id=session-456`

Get the message history for a specific chat session.

**Query Parameters:**
- `session_id`: The session identifier (required)
- `limit`: Maximum number of messages to return (optional, default: 100)

**Response:**
```json
{
  "status": {
    "success": true
  },
  "session": {
    "id": "session-456",
    "user_id": "user-123",
    "title": "Chat 2023-03-21 09:45",
    "created_at": "2023-03-21T09:45:32.123Z",
    "updated_at": "2023-03-21T10:15:44.567Z",
    "is_active": true
  },
  "messages": [
    {
      "id": "msg-111",
      "session_id": "session-456",
      "user_id": "user-123",
      "role": "user",
      "content": "สวัสดี",
      "created_at": "2023-03-21T09:45:32.123Z",
      "sequence": 1,
      "is_fortune": false
    },
    {
      "id": "msg-112",
      "session_id": "session-456",
      "user_id": "user-123",
      "role": "assistant",
      "content": "สวัสดีค่ะ มีอะไรให้ช่วยไหมคะ?",
      "created_at": "2023-03-21T09:45:35.456Z",
      "sequence": 2,
      "is_fortune": false
    }
  ],
  "count": 2
}
```

### Create a New Session

#### `POST /chat/new-session`

Create a new chat session.

**Request Body:**
```json
{
  "user_id": "user-123",
  "title": "Fortune Reading Session"
}
```

**Response:**
```json
{
  "status": {
    "success": true
  },
  "message": "New session created",
  "session": {
    "id": "session-789",
    "user_id": "user-123",
    "title": "Fortune Reading Session",
    "created_at": "2023-03-21T11:30:22.123Z",
    "updated_at": "2023-03-21T11:30:22.123Z",
    "is_active": true
  }
}
```

### Update Session Title

#### `PUT /chat/session/{session_id}/title`

Update the title of a chat session.

**Request Body:**
```json
{
  "title": "Updated Session Title"
}
```

**Response:**
```json
{
  "status": {
    "success": true
  },
  "message": "Session title updated",
  "session": {
    "id": "session-456",
    "user_id": "user-123",
    "title": "Updated Session Title",
    "created_at": "2023-03-21T09:45:32.123Z",
    "updated_at": "2023-03-21T11:35:44.567Z",
    "is_active": true
  }
}
```

### End a Session

#### `POST /chat/end-session`

Mark a chat session as inactive.

**Request Body:**
```json
{
  "session_id": "session-456"
}
```

**Response:**
```json
{
  "status": {
    "success": true
  },
  "message": "Session session-456 marked as inactive",
  "session": {
    "id": "session-456",
    "user_id": "user-123",
    "title": "Chat 2023-03-21 09:45",
    "created_at": "2023-03-21T09:45:32.123Z",
    "updated_at": "2023-03-21T11:40:15.789Z",
    "is_active": false
  }
}
```

### Delete a Session

#### `DELETE /chat/session/{session_id}`

Delete a chat session and all its messages.

**Response:**
```json
{
  "status": {
    "success": true
  },
  "message": "Session session-456 deleted"
}
```

## Fortune Telling API Endpoints

### Calculate Thai Fortune

#### `POST /fortune`

Calculate Thai fortune (7N9B) based on birthdate.

**Request Body:**
```json
{
  "birthdate": "1990-05-15",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "status": {
    "success": true
  },
  "user_id": "user-123",
  "request_id": "req-uuid",
  "result": {
    "bases": {
      "base1": {
        "อัตตะ": 3,
        "หินะ": 4,
        "ธานัง": 5,
        "ปิตา": 6,
        "มาตา": 7,
        "โภคา": 1,
        "มัชฌิมา": 2
      },
      "base2": {
        "ตะนุ": 6,
        "กดุมภะ": 7,
        "สหัชชะ": 1,
        "พันธุ": 2,
        "ปุตตะ": 3,
        "อริ": 4,
        "ปัตนิ": 5
      },
      "base3": {
        "มรณะ": 1,
        "สุภะ": 2,
        "กัมมะ": 3,
        "ลาภะ": 4,
        "พยายะ": 5,
        "ทาสา": 6,
        "ทาสี": 7
      },
      "base4": [10, 13, 9, 12, 15, 11, 14]
    },
    "individual_interpretations": [
      {
        "category": "มาตา",
        "meaning": "แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว",
        "influence": "กลาง",
        "value": 7,
        "heading": "ระดับอิทธิพลของมาตา: 7",
        "detail": "มาตา(แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว) มีอิทธิพลอย่างมากในเรื่องชีวิตของคุณ เรื่องนี้มีความสำคัญมากในช่วงนี้"
      },
      /* Additional interpretations... */
    ],
    "combination_interpretations": [
      {
        "category": "มาตา-กดุมภะ",
        "heading": "ความสัมพันธ์ที่แข็งแกร่งระหว่างมาตาและกดุมภะ",
        "meaning": "มาตา(แม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว) มีอิทธิพลอย่างมากในเรื่องชีวิตของคุณ และกดุมภะ(รายได้รายจ่าย) มีอิทธิพลอย่างมากในเรื่องชีวิตของคุณเช่นกัน ทำให้เห็นว่าสองด้านนี้มีความสำคัญมากในชีวิตของคุณในช่วงนี้",
        "influence": "ดี"
      },
      /* Additional combination interpretations... */
    ],
    "summary": "จากวันเกิดของคุณ พบว่าฐานหลักที่มีอิทธิพลสูงสุดคือ มาตา (7), กดุมภะ (7), และทาสี (7) ซึ่งเกี่ยวข้องกับแม่หรือผู้ใหญ่ เรื่องในบ้าน เรื่องส่วนตัว, รายได้รายจ่าย, และการเหน็จเหนื่อยเพื่อตัวเอง \n\nการตีความที่สำคัญ:\n- ความสัมพันธ์ที่แข็งแกร่งระหว่างมาตาและกดุมภะ\n- ความสัมพันธ์ที่แข็งแกร่งระหว่างมาตาและทาสี\n- ความสัมพันธ์ที่แข็งแกร่งระหว่างกดุมภะและทาสี"
  },
  "timestamp": 1677858242
}
```

### Get Fortune System Explanation

#### `GET /fortune/explanation`

Get an explanation of the Thai fortune (7N9B) system.

**Response:**
```json
{
  "status": {
    "success": true
  },
  "data": {
    "system_name": "เลข 7 ฐาน 9 (7N9B)",
    "description": "เลข 7 ฐาน 9 คือศาสตร์การทำนายโชคชะตาโบราณของไทย โดยใช้วันเกิดคำนวณตัวเลขและความหมายต่างๆ",
    "bases": {
      "base1": "เกี่ยวกับวันเกิด - อัตตะ, หินะ, ธานัง, ปิตา, มาตา, โภคา, มัชฌิมา",
      "base2": "เกี่ยวกับเดือนเกิด - ตะนุ, กดุมภะ, สหัชชะ, พันธุ, ปุตตะ, อริ, ปัตนิ",
      "base3": "เกี่ยวกับปีเกิด - มรณะ, สุภะ, กัมมะ, ลาภะ, พยายะ, ทาสา, ทาสี",
      "base4": "ผลรวมของฐาน 1-3"
    },
    "interpretation": "ตัวเลขที่สูงในแต่ละฐานแสดงถึงอิทธิพลที่มีผลต่อชีวิตในด้านนั้นๆ"
  },
  "timestamp": 1677858242
}
```

## Frontend Implementation Guide

### 1. Managing Chat Sessions

1. **Initialize a new user:**
   - Generate a UUID for the user if they don't have one already
   - Store this in localStorage or your state management system

2. **Start a conversation:**
   - Send a request to `/chat/message` with the user's first message
   - The API will automatically create a new session if needed
   - Store the returned `session_id` for subsequent messages

3. **Continue a conversation:**
   - Include the `session_id` with each message to maintain conversation context

4. **List available sessions:**
   - Use `/chat/sessions` to get all sessions for a user
   - Display these in your UI as conversation history

5. **Load conversation history:**
   - When a user selects a session, use `/chat/history` to load all previous messages
   - Display this in your chat UI

### 2. Implementing Chat UI

#### Basic Chat Implementation:

```javascript
// Example using fetch API
async function sendMessage(message, userId, sessionId = null) {
  const response = await fetch('https://your-api-base-url.com/api/v1/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      session_id: sessionId,
      stream: false
    }),
  });
  
  return await response.json();
}

// Usage
const userId = localStorage.getItem('userId') || generateUUID();
let sessionId = localStorage.getItem('currentSessionId');

// Send message and update UI with response
const sendBtn = document.getElementById('send-btn');
sendBtn.addEventListener('click', async () => {
  const messageInput = document.getElementById('message-input');
  const message = messageInput.value;
  
  // Add user message to UI
  addMessageToUI('user', message);
  messageInput.value = '';
  
  // Send to API
  const response = await sendMessage(message, userId, sessionId);
  
  // Update session ID if this is a new conversation
  if (!sessionId) {
    sessionId = response.session_id;
    localStorage.setItem('currentSessionId', sessionId);
  }
  
  // Add assistant response to UI
  const assistantMessage = response.response.choices[0].message.content;
  addMessageToUI('assistant', assistantMessage);
});
```

#### WebSocket Chat Implementation:

```javascript
class ChatWebSocket {
  constructor(baseUrl, userId, sessionId = null) {
    this.userId = userId;
    this.sessionId = sessionId;
    this.ws = null;
    this.baseUrl = baseUrl; 
    this.messageCallbacks = {};
    this.onConnectionCallback = null;
    this.onErrorCallback = null;
    this.connected = false;
    this.currentMessageId = null;
    this.pendingMessages = [];
    this.responseBuffer = {};
  }
  
  connect() {
    // Create WebSocket connection
    this.ws = new WebSocket(`${this.baseUrl}/api/v1/ws/chat`);
    
    this.ws.onopen = () => {
      // Send connection parameters when socket opens
      this.ws.send(JSON.stringify({
        user_id: this.userId,
        session_id: this.sessionId
      }));
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.event === 'connected') {
        this.connected = true;
        this.sessionId = data.session_id;
        
        // Process any pending messages
        if (this.pendingMessages.length > 0) {
          this.pendingMessages.forEach(msg => this.sendMessage(msg));
          this.pendingMessages = [];
        }
        
        if (this.onConnectionCallback) {
          this.onConnectionCallback(data);
        }
      }
      else if (data.event === 'message_received') {
        this.currentMessageId = data.message_id;
        // Initialize buffer for this message
        this.responseBuffer[this.currentMessageId] = '';
      }
      else if (data.event === 'chunk') {
        // Add chunk to buffer
        this.responseBuffer[data.message_id] += data.content;
        
        // Call the callback with current data
        if (this.messageCallbacks[data.message_id]) {
          this.messageCallbacks[data.message_id]({
            type: 'chunk',
            content: data.content,
            fullContent: this.responseBuffer[data.message_id]
          });
        }
      }
      else if (data.event === 'complete') {
        // Ensure we have the complete message
        if (this.messageCallbacks[data.message_id]) {
          this.messageCallbacks[data.message_id]({
            type: 'complete',
            content: data.content
          });
          
          // Clean up callback and buffer
          delete this.messageCallbacks[data.message_id];
          delete this.responseBuffer[data.message_id];
        }
      }
      else if (data.event === 'error') {
        if (this.onErrorCallback) {
          this.onErrorCallback(data.error);
        }
      }
    };
    
    this.ws.onerror = (error) => {
      if (this.onErrorCallback) {
        this.onErrorCallback("WebSocket error: " + JSON.stringify(error));
      }
    };
    
    this.ws.onclose = () => {
      this.connected = false;
      
      // Attempt to reconnect after delay
      setTimeout(() => {
        if (!this.connected) {
          this.connect();
        }
      }, 3000);
    };
  }
  
  sendMessage(message) {
    if (!this.connected) {
      this.pendingMessages.push(message);
      return null;
    }
    
    const messageId = Date.now().toString();
    
    // Send the message
    this.ws.send(JSON.stringify({
      message: message
    }));
    
    return messageId;
  }
  
  onMessageUpdate(messageId, callback) {
    this.messageCallbacks[messageId] = callback;
  }
  
  onConnection(callback) {
    this.onConnectionCallback = callback;
  }
  
  onError(callback) {
    this.onErrorCallback = callback;
  }
  
  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage example:
const userId = localStorage.getItem('userId') || generateUUID();
let sessionId = localStorage.getItem('currentSessionId');

const chatSocket = new ChatWebSocket('wss://your-api-base-url.com', userId, sessionId);

// Connect to WebSocket
chatSocket.connect();

// Handle connection event
chatSocket.onConnection((data) => {
  console.log('Connected to chat WebSocket:', data);
  sessionId = data.session_id;
  localStorage.setItem('currentSessionId', sessionId);
});

// Handle errors
chatSocket.onError((error) => {
  console.error('WebSocket error:', error);
});

// Send a message
document.getElementById('send-btn').addEventListener('click', () => {
  const messageInput = document.getElementById('message-input');
  const message = messageInput.value;
  
  // Add user message to UI
  addMessageToUI('user', message);
  messageInput.value = '';
  
  // Send via WebSocket
  const messageId = chatSocket.sendMessage(message);
  
  // Create placeholder for assistant response
  const responseContainer = document.createElement('div');
  responseContainer.className = 'assistant-message';
  responseContainer.id = `response-${messageId}`;
  document.getElementById('chat-container').appendChild(responseContainer);
  
  // Handle streaming response
  chatSocket.onMessageUpdate(messageId, (data) => {
    if (data.type === 'chunk') {
      // Update UI with each chunk
      responseContainer.textContent = data.fullContent;
    } else if (data.type === 'complete') {
      // Ensure we have the complete message
      responseContainer.textContent = data.content;
    }
  });
});
```

#### Server-Sent Events (SSE) Implementation:

```javascript
// Using native EventSource API for better compatibility
function streamChatWithEventSource(message, userId, sessionId = null) {
  // Build query parameters
  const params = new URLSearchParams({
    message: message
  });
  
  if (userId) params.append('user_id', userId);
  if (sessionId) params.append('session_id', sessionId);
  
  // Create EventSource connection - USING GET METHOD
  const eventSource = new EventSource(`https://your-api-base-url.com/api/v1/chat/stream?${params}`);
  
  // Create placeholder for assistant response
  const responseContainer = document.createElement('div');
  responseContainer.className = 'assistant-message';
  document.getElementById('chat-container').appendChild(responseContainer);
  
  let fullResponse = '';
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.status === 'streaming') {
      fullResponse += data.content;
      responseContainer.textContent = fullResponse;
      
      // Update session ID if needed
      if (!sessionId && data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('currentSessionId', sessionId);
      }
    } else if (data.status === 'complete') {
      // Ensure we have the complete message
      if (data.complete_response) {
        responseContainer.textContent = data.complete_response;
      }
      eventSource.close();
    } else if (data.status === 'error') {
      responseContainer.innerHTML = `<span class="error">Error: ${data.message || 'Unknown error'}</span>`;
      eventSource.close();
    }
  };
  
  eventSource.onerror = () => {
    responseContainer.innerHTML += '<span class="error">Connection error. Please try again.</span>';
    eventSource.close();
  };
  
  // Return the EventSource instance so it can be closed if needed
  return eventSource;
}

// Usage
document.getElementById('send-btn').addEventListener('click', () => {
  const messageInput = document.getElementById('message-input');
  const message = messageInput.value;
  const userId = localStorage.getItem('userId') || generateUUID();
  const sessionId = localStorage.getItem('currentSessionId');
  
  // Add user message to UI
  addMessageToUI('user', message);
  messageInput.value = '';
  
  // Stream response with EventSource
  streamChatWithEventSource(message, userId, sessionId);
});
```

### 3. Implementing Fortune Telling Feature

```javascript
async function calculateFortune(birthdate, userId) {
  const response = await fetch('https://your-api-base-url.com/api/v1/fortune', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      birthdate: birthdate,
      user_id: userId
    }),
  });
  
  return await response.json();
}

// Usage in a form
document.getElementById('fortune-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const birthdate = document.getElementById('birthdate').value;
  const userId = localStorage.getItem('userId') || generateUUID();
  
  const fortuneResult = await calculateFortune(birthdate, userId);
  
  // Display the fortune result
  displayFortuneResult(fortuneResult);
});

function displayFortuneResult(result) {
  const container = document.getElementById('fortune-result');
  
  // Display summary
  container.innerHTML = `<h2>สรุปการทำนาย</h2><p>${result.result.summary}</p>`;
  
  // Display bases
  container.innerHTML += '<h3>ฐานตัวเลข</h3>';
  Object.entries(result.result.bases.base1).forEach(([category, value]) => {
    container.innerHTML += `<div class="fortune-item"><span>${category}</span>: <span class="value">${value}</span></div>`;
  });
  
  // Display individual interpretations
  container.innerHTML += '<h3>การตีความรายฐาน</h3>';
  result.result.individual_interpretations.forEach(item => {
    container.innerHTML += `
      <div class="interpretation-item">
        <h4>${item.heading}</h4>
        <p>${item.detail}</p>
      </div>
    `;
  });
  
  // Display combination interpretations
  container.innerHTML += '<h3>การตีความเชื่อมโยง</h3>';
  result.result.combination_interpretations.forEach(item => {
    container.innerHTML += `
      <div class="interpretation-item">
        <h4>${item.heading}</h4>
        <p>${item.meaning}</p>
        <span class="influence ${item.influence}">อิทธิพล: ${item.influence}</span>
      </div>
    `;
  });
}
```

## Error Handling

All endpoints return a consistent error format:

```json
{
  "status": {
    "success": false,
    "message": "Error message here",
    "error_code": 400
  }
}
```

Common HTTP status codes:
- `400`: Bad Request - Invalid parameters
- `404`: Not Found - Resource not found
- `500`: Internal Server Error - Server-side issue

Make sure to handle these errors in your frontend application to provide appropriate feedback to users.

## Conclusion

This API provides a comprehensive set of endpoints for building a Thai fortune telling and chat application. The session management system allows for persistent conversations across user sessions, and the fortune telling feature provides detailed interpretations based on Thai astrology.

For questions or issues, please contact the API development team.
