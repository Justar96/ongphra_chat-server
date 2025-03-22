# LangChain RAG Fortune Teller

This module provides a LangChain-powered Retrieval Augmented Generation (RAG) tool for Thai fortune telling based on birthdates using the 7-base-9 numerology system.

## Features

- Calculate fortune data based on a birthdate (YYYY-MM-DD format)
- Enhance interpretations with RAG using a vector database of fortune insights
- Return structured JSON results with fortune calculation and RAG-enhanced interpretations
- Works with the existing chat API to provide natural language responses

## How It Works

1. **Fortune Calculation**: The system calculates numerological values from the birthdate using the Thai 7-base-9 system
2. **RAG Enhancement**: LangChain retrieves relevant interpretations from a pre-built knowledge base
3. **Result Generation**: The combined data is structured as JSON and can be presented to the user as a natural language response

## Usage

### Via API

Send a chat message containing a birthdate to the chat endpoint:

```
POST /chat/message
{
  "message": "ดูดวงจากวันเกิด 1990-01-15",
  "user_id": "user123",
  "session_id": "session456"
}
```

### Programmatically

```python
from app.utils.tool_handler import tool_handler

# Execute the fortune tool
result = await tool_handler.execute_tool(
    "fortune_calculator",
    birthdate="1990-01-15",
    detail_level="normal"  # Options: "simple", "normal", "detailed"
)

# Access the result
if not result.error:
    fortune_data = result.result.get("fortune", {})
    
    # Access RAG interpretations
    rag_interps = fortune_data.get("rag_interpretations", [])
    for interp in rag_interps:
        print(f"Category: {interp.get('category')} - {interp.get('interpretation')}")
```

## Knowledge Base

The RAG system uses a FAISS vector database with embeddings from OpenAI. The knowledge base contains:

- Individual category interpretations (high and low values)
- Combination interpretations between categories
- Influence descriptions and meanings

## Sample JSON Response

```json
{
  "status": "success",
  "fortune": {
    "birthdate": "15 January 1990",
    "day_of_week": "จันทร์",
    "zodiac_year": "เสือ",
    "bases": { "base1": 1, "base2": 7, "base3": 4 },
    "top_categories": {
      "base1": { "name": "attana", "thai_name": "อัตตะ", "meaning": "ตัวท่านเอง", "value": 7 },
      "base2": { "name": "patni", "thai_name": "ปัตนิ", "meaning": "คู่ครอง", "value": 7 },
      "base3": { "name": "labha", "thai_name": "ลาภะ", "meaning": "ลาภยศ โชคลาภ", "value": 6 }
    },
    "pairs": [
      {
        "heading": "ความสัมพันธ์ระหว่างอัตตะและปัตนิ",
        "meaning": "คุณมีความโดดเด่นในเรื่องอัตตะและปัตนิ ซึ่งส่งผลดีต่อชีวิตของคุณ"
      }
    ],
    "summary": "จากวันเกิด 15 January 1990 (จันทร์) เสือ พบว่า...",
    "rag_interpretations": [
      {
        "category": "attana",
        "value": 7,
        "interpretation": "High values (5-7) in attana (อัตตะ) indicate strong self-confidence and individuality."
      }
    ]
  }
}
```

## Extending the Knowledge Base

To extend the knowledge base with more interpretations:

1. Add new documents to the `fortune_knowledge` list in `app/utils/tool_handler.py`
2. Restart the application to rebuild the vector database

## Dependencies

- LangChain core and community packages
- FAISS for vector storage
- OpenAI for embeddings
- The existing fortune calculation system 