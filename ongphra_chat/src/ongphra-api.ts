/**
 * Ongphra Chat API Client
 * This file handles communication with the Ongphra Chat API
 */

// API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Types
export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  timestamp?: string;
  toolData?: any;
}

export interface ChatSession {
  id: string;
  title: string;
  user_id: string;
  created_at: string;
  is_active: boolean;
  message_count?: number;
}

// Utility to generate a UUID (simplified version)
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Utility to safely access localStorage
export function getLocalStorage(key: string): string | null {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null;
  }
  return localStorage.getItem(key);
}

export function setLocalStorage(key: string, value: string): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }
  localStorage.setItem(key, value);
}

// Utility to get or create a user ID
export function getUserId(): string {
  const storedUserId = getLocalStorage('ongphra_user_id');
  if (storedUserId) {
    return storedUserId;
  }
  
  const newUserId = generateUUID();
  setLocalStorage('ongphra_user_id', newUserId);
  return newUserId;
}

// Utility to get the current session ID
export function getSessionId(): string | null {
  return getLocalStorage('ongphra_session_id');
}

// Utility to set the current session ID
export function setSessionId(sessionId: string): void {
  setLocalStorage('ongphra_session_id', sessionId);
}

/**
 * Send a chat message using HTTP streaming
 */
export async function sendChatMessage(
  message: string, 
  onChunk?: (chunk: string) => void,
  onComplete?: (fullResponse: string) => void,
  onError?: (error: string) => void
): Promise<any> {
  try {
    // Get user and session IDs
    const currentUserId = getUserId();
    const currentSessionId = getSessionId();
    
    // Create request payload
    const payload = {
      message,
      user_id: currentUserId,
      session_id: currentSessionId,
      stream: !!onChunk // Use streaming if onChunk handler is provided
    };
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    // Handle error response
    if (!response.ok) {
      const errorData = await response.json();
      if (onError) onError(errorData.detail || 'Error sending message');
      return null;
    }
    
    // Handle streaming response
    if (onChunk && response.headers.get('content-type')?.includes('text/event-stream')) {
      const reader = response.body?.getReader();
      let fullResponse = '';
      
      if (reader) {
        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim());
          
          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              if (data.content) {
                onChunk(data.content);
                fullResponse += data.content;
              }
            } catch (e) {
              console.warn('Error parsing chunk:', line);
            }
          }
        }
        
        if (onComplete) onComplete(fullResponse);
        return fullResponse;
      }
    }
    
    // Handle regular response
    const data = await response.json();
    const content = data.response?.choices?.[0]?.message?.content || '';
    
    // Save the session ID if it was created
    if (data.session_id && !currentSessionId) {
      setSessionId(data.session_id);
    }
    
    if (onComplete) onComplete(content);
    return data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    if (onError) onError('Network error. Please try again.');
    return null;
  }
}

/**
 * Get user's chat sessions
 */
export async function getUserSessions(customUserId?: string): Promise<ChatSession[]> {
  try {
    const userId = customUserId || getUserId();
    const response = await fetch(`${API_BASE_URL}/chat/sessions?user_id=${userId}`);
    
    if (!response.ok) return [];
    
    const data = await response.json();
    return data.sessions || [];
  } catch (error) {
    console.error('Error fetching user sessions:', error);
    return [];
  }
}

/**
 * Get chat history for a session
 */
export async function getChatHistory(sessionId: string): Promise<ChatMessage[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/history?session_id=${sessionId}`);
    
    if (!response.ok) return [];
    
    const data = await response.json();
    return data.messages || [];
  } catch (error) {
    console.error('Error fetching chat history:', error);
    return [];
  }
}

/**
 * Create a new chat session
 */
export async function createNewSession(title?: string): Promise<ChatSession | null> {
  try {
    const userId = getUserId();
    const response = await fetch(`${API_BASE_URL}/chat/new-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        title
      })
    });
    
    if (!response.ok) return null;
    
    const data = await response.json();
    if (data.session) {
      setSessionId(data.session.id);
      return data.session;
    }
    
    return null;
  } catch (error) {
    console.error('Error creating new session:', error);
    return null;
  }
} 