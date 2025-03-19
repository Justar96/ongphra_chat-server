# Chat Session History

The Chat Session History feature provides persistent storage for chat conversations, allowing for better data analysis, user experience improvements, and long-term conversation tracking.

## Features

- **Persistent Message Storage**: All chat messages are saved to a database
- **Session Management**: Conversations are organized into sessions
- **User Association**: Messages are linked to specific users
- **Fortune Reading Tracking**: Special tracking for fortune reading messages
- **API Access**: Endpoints to retrieve and manage chat history

## Database Schema

The feature uses two main tables:

### chat_sessions

Stores metadata about chat sessions:

| Column      | Type          | Description                             |
|-------------+---------------+-----------------------------------------|
| id          | VARCHAR(36)   | Unique session identifier               |
| user_id     | VARCHAR(100)  | User identifier                         |
| created_at  | TIMESTAMP     | When the session was created            |
| updated_at  | TIMESTAMP     | When the session was last updated       |
| is_active   | BOOLEAN       | Whether the session is currently active |
| session_data| JSON          | Additional session metadata             |

### chat_messages

Stores individual messages within chat sessions:

| Column      | Type          | Description                             |
|-------------+---------------+-----------------------------------------|
| id          | VARCHAR(36)   | Unique message identifier               |
| session_id  | VARCHAR(36)   | Session this message belongs to         |
| user_id     | VARCHAR(100)  | User identifier                         |
| role        | VARCHAR(20)   | Message role (user or assistant)        |
| content     | TEXT          | Message content                         |
| timestamp   | TIMESTAMP     | When the message was sent               |
| is_fortune  | BOOLEAN       | Whether this is a fortune reading       |
| metadata    | JSON          | Additional message metadata             |

## API Endpoints

### Session Management

- **GET** `/api/chat/sessions` - Get a list of chat sessions for a user
- **GET** `/api/chat/history` - Get chat history for a session
- **POST** `/api/chat/end-session` - Mark a session as inactive
- **DELETE** `/api/chat/session/{session_id}` - Delete a session and all messages

### Existing Endpoints (Updated)

- **POST** `/api/chat` - Now automatically saves messages to the database
- **POST** `/api/chat/stream` - Now automatically saves messages to the database
- **DELETE** `/api/session/{user_id}` - Now also handles database sessions

## Usage Examples

### Retrieving Chat Sessions

```bash
curl -X GET "http://localhost:8000/api/chat/sessions?user_id=user123&limit=5&active_only=true"
```

Response:
```json
{
  "success": true,
  "sessions": [
    {
      "id": "e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d",
      "user_id": "user123",
      "created_at": "2023-08-15T14:30:25",
      "updated_at": "2023-08-15T15:45:12",
      "is_active": true
    },
    ...
  ],
  "count": 5
}
```

### Retrieving Chat History

```bash
curl -X GET "http://localhost:8000/api/chat/history?user_id=user123&session_id=e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d&limit=10"
```

Response:
```json
{
  "success": true,
  "session": {
    "id": "e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d",
    "user_id": "user123",
    "created_at": "2023-08-15T14:30:25",
    "updated_at": "2023-08-15T15:45:12",
    "is_active": true
  },
  "messages": [
    {
      "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "session_id": "e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d",
      "user_id": "user123",
      "role": "user",
      "content": "Hello, can you tell me about my fortune?",
      "timestamp": "2023-08-15T14:30:25",
      "is_fortune": false
    },
    {
      "id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "session_id": "e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d",
      "user_id": "user123",
      "role": "assistant",
      "content": "I'd be happy to help with that! To give you an accurate fortune reading, I'll need your birth date...",
      "timestamp": "2023-08-15T14:30:30",
      "is_fortune": false
    },
    ...
  ],
  "count": 10
}
```

### Ending a Session

```bash
curl -X POST "http://localhost:8000/api/chat/end-session" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d"}'
```

Response:
```json
{
  "success": true,
  "message": "Session e7c6b2a8-3e4f-4a5b-9c0d-8e7f6a5b4c3d marked as inactive"
}
```

## Integration with Existing System

The chat history system has been integrated with the existing API endpoints:

1. The chat endpoints (`/api/chat` and `/api/chat/stream`) now automatically:
   - Save user messages to the database
   - Save assistant responses to the database
   - Track whether messages contain fortune readings
   - Return session IDs for frontend tracking

2. Session management is handled transparently:
   - New sessions are created when needed
   - Existing sessions are reused when a session ID is provided

## Setting Up

To set up the chat history system:

1. Run the database migration:
   ```bash
   python -m app.db.migrate
   ```

2. The system will automatically start storing chat history once the migration is applied.

## Data Retention

Consider implementing a data retention policy for chat history. Options include:

- Automatically anonymizing data after a certain period
- Setting up regular purges of old chat data
- Allowing users to request deletion of their chat history

Implement these policies based on your application's privacy requirements and data storage capacity.