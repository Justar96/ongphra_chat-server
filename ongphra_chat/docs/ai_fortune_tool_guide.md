# Fortune Reading Tool Guide for AI

This document explains how to use the Fortune Reading tool in the Ongphra Chat application.

## Purpose

The Fortune Reading tool helps the AI determine when a user is asking for a fortune reading, check if birth date information is available, and provide appropriate fortune readings based on the user's birth information and question.

## Key Features

1. **Fortune Request Detection**: Automatically detects if the user's message is requesting a fortune reading
2. **Birth Date Extraction**: Extracts birth date from messages when provided
3. **Session Management**: Maintains birth information across conversations
4. **Contextual Response**: Provides relevant fortune readings based on the user's question

## When to Use

Use this tool when:
- A user asks for their fortune, horoscope, or destiny
- A user mentions keywords related to fortune-telling or astrology
- A user asks questions about their future
- A user provides their birth date in a conversation

## How to Use

```python
# Sample pseudocode for AI implementation
async def handle_user_message(user_message, user_id):
    # Step 1: Check if the message is a fortune request
    fortune_result = await process_fortune_tool(user_message, user_id)
    
    # Step 2: Handle the response based on the result
    if fortune_result["is_fortune_request"]:
        # Step 2a: If we need birth date information, ask for it
        if fortune_result["needs_birthdate"]:
            return "I'd be happy to check your fortune. Could you please tell me your birth date? (DD/MM/YYYY)"
        
        # Step 2b: If we have a fortune reading, provide it
        if fortune_result["fortune_reading"]:
            reading = fortune_result["fortune_reading"]
            response = f"**{reading['heading']}**\n\n{reading['meaning']}"
            # Optional: Add information about influence type
            if reading["influence_type"]:
                influence_map = {
                    "ดี": "positive",
                    "ไม่ดี": "negative",
                    "ปานกลาง": "neutral"
                }
                influence = influence_map.get(reading["influence_type"], reading["influence_type"])
                response += f"\n\nThis reading indicates a {influence} influence on your life."
            return response
    
    # Step 3: If not a fortune request, handle normally
    return "Regular response for non-fortune request"
```

## Response Structure

The tool returns a dictionary with the following fields:

- `is_fortune_request` (boolean): Indicates if the message is asking for a fortune reading
- `needs_birthdate` (boolean): Indicates if we need to ask for birth date information
- `fortune_reading` (object or null): The fortune reading result if available
  - `birth_date` (string): Birth date used for the reading
  - `thai_day` (string): Thai day of the birth date
  - `question` (string): User's question
  - `heading` (string): Reading heading/title
  - `meaning` (string): Reading content
  - `influence_type` (string): Type of influence (positive, negative, neutral)
- `user_message` (string): Original user message
- `extracted_birthdate` (string or null): Birth date extracted from message if found

## Example Conversation Flow

### Scenario 1: User asks for fortune without providing birth date

```
User: "I want to know my fortune"
AI: [Uses tool, sees needs_birthdate=true]
AI: "I'd be happy to check your fortune. Could you please tell me your birth date? (DD/MM/YYYY)"

User: "I was born on 14/02/1996"
AI: [Uses tool, sees fortune_reading is available]
AI: "**Your Career Path**

Your birth chart shows a strong influence in the house of career. You have natural leadership abilities and tend to excel in positions of authority..."
```

### Scenario 2: User asks for fortune after already providing birth date

```
User: "What does my future hold for my love life?"
AI: [Uses tool, sees fortune_reading is available]
AI: "**Relationship Harmony**

Your birth chart indicates a favorable period for relationships. You may find that existing relationships deepen and new connections form naturally..."
```

## Best Practices

1. Always check `is_fortune_request` first to determine if this is a fortune-related question
2. If `needs_birthdate` is true, ask the user for their birth date in a natural, conversational way
3. When presenting the fortune reading, format it nicely with the heading as a title
4. Maintain context across the conversation - the tool handles this automatically through the session
5. Don't ask for birth date again if it's already been provided in previous messages

## Error Handling

If the tool returns an error field, respond gracefully:

```python
if "error" in fortune_result:
    return "I apologize, but I'm having trouble processing your fortune reading request. Could you please try again?"
``` 