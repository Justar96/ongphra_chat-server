# app/main.py

"""
Ongphra Chat API - Main Application

This application provides fortune telling and AI chat capabilities with the following endpoints:

1. `/api/chat` - Main chat endpoint that supports both regular conversation and fortune readings
   - Uses AI with memory to maintain context across conversations
   - Automatically detects and processes fortune reading requests when enabled
   - Parameters include: prompt, birth_date (optional), thai_day (optional), enable_fortune (default: true)

2. `/api/chat/stream` - Streaming version of the chat endpoint
   - Same functionality as the regular chat endpoint, but streams responses
   - Better user experience for long responses
"""
