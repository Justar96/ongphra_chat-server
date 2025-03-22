import httpx
import json
import asyncio

async def test_fortune_rag():
    """Test the fortune telling RAG functionality."""
    # Set up log file
    log_file = "fortune_test_log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Starting Fortune RAG test...\n\n")
    
    # Set up the request
    url = "http://localhost:8000/api/v1/chat/message"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token"
    }
    
    # Test message with birthdate
    payload = {
        "message": "ขอดูดวงชะตาจากวันเกิด 1990-01-15 หน่อยค่ะ",
        "user_id": "test_user",
        "session_id": "test_session"
    }
    
    try:
        # Send the request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                
                # Save the result to file
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write("Success! Response received:\n")
                    f.write(json.dumps(result, indent=2, ensure_ascii=False))
                    f.write("\n\n")
                
                # Check if fortune tool was used
                if "ดวงชะตา" in result.get("response", ""):
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("✅ Fortune teller working properly!\n")
                    
                    # Check if RAG interpretations are included
                    if "ข้อมูลเชิงลึกเพิ่มเติม" in result.get("response", ""):
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write("✅ RAG enrichment working properly!\n")
                    else:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write("❌ RAG enrichment not detected in the response\n")
                else:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("❌ Fortune teller may not be working properly\n")
            else:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"Error: Status code {response.status_code}\n")
                    f.write(response.text)
                    f.write("\n")
    except Exception as e:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"Error testing fortune teller: {str(e)}\n")

    # Save full response to file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\nTest completed. Check fortune_test_log.txt for results.\n")

if __name__ == "__main__":
    asyncio.run(test_fortune_rag()) 