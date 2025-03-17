let socket;
let isConnected = false;
let isGeneralMode = false;
let eventSource = null;

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
        isGeneralMode = false;
        document.getElementById('status-indicator').textContent = 'Connected';
        document.getElementById('status-indicator').style.color = 'green';
        document.getElementById('connect-btn').disabled = true;
        document.getElementById('general-btn').disabled = true;
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
                messageElement.querySelector('.message-content').textContent += data.content;
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
        disconnectAll();
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        addMessage('System', 'Error connecting to fortune telling service.', 'bot-message');
        disconnectAll();
    };
}

function connectGeneralChat() {
    // Get language and streaming preferences
    const language = document.getElementById('language').value;
    const streamMode = document.getElementById('stream-mode').checked;
    
    // Set up UI
    isConnected = true;
    isGeneralMode = true;
    document.getElementById('status-indicator').textContent = 'Connected (General Mode)';
    document.getElementById('status-indicator').style.color = 'green';
    document.getElementById('connect-btn').disabled = true;
    document.getElementById('general-btn').disabled = true;
    document.getElementById('disconnect-btn').disabled = false;
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    
    // Add system message
    addMessage('System', 'Connected to general fortune telling service. You can ask general questions about Thai astrology.', 'bot-message');
}

function disconnectAll() {
    if (socket && !isGeneralMode) {
        socket.close();
        socket = null;
    }
    
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    
    isConnected = false;
    isGeneralMode = false;
    document.getElementById('status-indicator').textContent = 'Disconnected';
    document.getElementById('status-indicator').style.color = 'red';
    document.getElementById('connect-btn').disabled = false;
    document.getElementById('general-btn').disabled = false;
    document.getElementById('disconnect-btn').disabled = true;
    document.getElementById('message-input').disabled = true;
    document.getElementById('send-btn').disabled = true;
    
    // Add system message
    addMessage('System', 'Disconnected from fortune telling service.', 'bot-message');
}

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (message && isConnected) {
        // Add user message to chat
        addMessage('You', message, 'user-message');
        
        if (isGeneralMode) {
            // Send message to general endpoint
            sendGeneralQuestion(message);
        } else {
            // Send message to WebSocket
            socket.send(JSON.stringify({ question: message }));
        }
        
        // Clear input
        messageInput.value = '';
    }
}

function sendGeneralQuestion(question) {
    const language = document.getElementById('language').value;
    const streamMode = document.getElementById('stream-mode').checked;
    
    if (streamMode) {
        // Use Server-Sent Events for streaming
        if (eventSource) {
            eventSource.close();
        }
        
        // Create a unique ID for this message
        const messageId = 'msg-' + Date.now();
        
        // Add placeholder for streaming response
        addMessage('Fortune Teller', '', 'bot-message streaming', messageId);
        
        // Create EventSource
        const params = new URLSearchParams({
            question: question,
            language: language,
            stream: 'true'
        });
        
        eventSource = new EventSource(`/general-question?${params.toString()}`);
        
        // Handle start event
        eventSource.addEventListener('start', function(event) {
            console.log('Streaming started');
        });
        
        // Handle message event
        eventSource.addEventListener('message', function(event) {
            const data = JSON.parse(event.data);
            const messageElement = document.getElementById(messageId);
            
            if (data.type === 'chunk' && messageElement) {
                messageElement.querySelector('.message-content').textContent += data.content;
            }
        });
        
        // Handle end event
        eventSource.addEventListener('end', function(event) {
            const messageElement = document.getElementById(messageId);
            if (messageElement) {
                messageElement.classList.remove('streaming');
            }
            eventSource.close();
            eventSource = null;
        });
        
        // Handle errors
        eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            eventSource.close();
            eventSource = null;
            
            // Remove streaming class
            const streamingElement = document.querySelector('.message.streaming');
            if (streamingElement) {
                streamingElement.classList.remove('streaming');
            }
        };
    } else {
        // Use regular AJAX for non-streaming
        fetch('/general-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'question': question,
                'language': language,
                'stream': 'false'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.fortune) {
                addMessage('Fortune Teller', data.fortune, 'bot-message');
            } else if (data.error) {
                addMessage('System', 'Error: ' + data.error, 'bot-message');
            }
        })
        .catch(error => {
            console.error('Error sending general question:', error);
            addMessage('System', 'Error sending question. Please try again.', 'bot-message');
        });
    }
}

function addMessage(sender, content, className, id = null) {
    const chatMessages = document.querySelector('.chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${className}`;
    if (id) {
        messageElement.id = id;
    }
    
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
    document.getElementById('general-btn').addEventListener('click', connectGeneralChat);
    document.getElementById('disconnect-btn').addEventListener('click', disconnectAll);
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    
    // Send message on Enter key
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
        