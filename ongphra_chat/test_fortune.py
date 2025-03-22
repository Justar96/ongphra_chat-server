import requests
import json
import time
import uuid
from app.utils.fortune_tool import calculate_fortune

def generate_id():
    return str(uuid.uuid4())

# Test fortune calculation
def test_fortune_calculation():
    url = "http://localhost:8000/api/v1/fortune"
    user_id = generate_id()
    payload = {"birthdate": "1990-01-01", "user_id": user_id}
    
    response = requests.post(url, json=payload)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['status']['success']}")
        print(f"User ID: {result['user_id']}")
        print(f"Request ID: {result['request_id']}")
        print(f"Summary: {result['result']['summary']}")
        # Print some example interpretations
        print("\nSample interpretations:")
        for interpretation in result['result']['individual_interpretations'][:3]:
            print(f"- {interpretation['category']} ({interpretation['value']}): {interpretation['heading']}")
    else:
        print(f"Error: {response.text}")

# Test fortune explanation
def test_fortune_explanation():
    url = "http://localhost:8000/api/v1/fortune/explanation"
    
    response = requests.get(url)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result['status']['success']}")
        print(f"System name: {result['data']['system_name']}")
        print(f"Description: {result['data']['description']}")
    else:
        print(f"Error: {response.text}")

# Test chat with normal endpoint
def test_normal_chat():
    url = "http://localhost:8000/api/v1/chat"
    user_id = generate_id()
    session_id = generate_id()
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "สวัสดี ช่วยแนะนำตัวเองหน่อยครับ"
            }
        ],
        "stream": False,
        "user_id": user_id,
        "session_id": session_id
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        
        # Print structure for debugging
        print(f"Response keys: {list(result.keys())}")
        
        # Handle different response structures
        if 'status' in result:
            # New standardized format
            print(f"Success: {result['status']['success']}")
            print(f"User ID: {result['user_id']}")
            print(f"Session ID: {result['session_id']}")
            print(f"Message ID: {result['message_id']}")
            
            # Extract content
            assistant_message = result['response']['choices'][0]['message']['content']
            print(f"Assistant response: {assistant_message}")
        else:
            # Old format
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"User ID: {result.get('user_id', 'N/A')}")
            print(f"Session ID: {result.get('session_id', 'N/A')}")
            
            if 'choices' in result:
                assistant_message = result['choices'][0]['message']['content']
                print(f"Assistant response: {assistant_message}")
            elif 'response' in result and 'choices' in result['response']:
                assistant_message = result['response']['choices'][0]['message']['content'] 
                print(f"Assistant response: {assistant_message}")
            else:
                print(f"Cannot find assistant message in response: {json.dumps(result, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

# Test fortune chat
def test_fortune_chat():
    url = "http://localhost:8000/api/v1/chat"  # Use the main chat endpoint
    user_id = generate_id()
    session_id = generate_id()
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "ฉันอยากดูดวงตามหลักเลข 7 ฐาน 9 ค่ะ"
            }
        ],
        "stream": False,
        "user_id": user_id,
        "session_id": session_id
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        
        # Print structure for debugging
        print(f"Response keys: {list(result.keys())}")
        
        # Handle different response structures
        if 'status' in result:
            # New standardized format
            print(f"Success: {result['status']['success']}")
            print(f"User ID: {result['user_id']}")
            print(f"Session ID: {result['session_id']}")
            print(f"Message ID: {result['message_id']}")
            
            # Extract content
            assistant_message = result['response']['choices'][0]['message']['content']
            print(f"Assistant response: {assistant_message}")
        else:
            # Old format or direct OpenAI response
            print(f"Direct API response detected")
            if 'choices' in result:
                assistant_message = result['choices'][0]['message']['content']
                print(f"Assistant response: {assistant_message}")
            else:
                print(f"Cannot find assistant message in response: {json.dumps(result, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

# Test chat with message endpoint
def test_chat_message():
    url = "http://localhost:8000/api/v1/chat/message"
    user_id = generate_id()
    session_id = generate_id()
    
    payload = {
        "message": "สวัสดี ช่วยแนะนำตัวเองหน่อยครับ",
        "user_id": user_id,
        "session_id": session_id,
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        
        # Print structure for debugging
        print(f"Response keys: {list(result.keys())}")
        
        # Handle different response structures
        if 'status' in result:
            # New standardized format
            print(f"Success: {result['status']['success']}")
            print(f"User ID: {result['user_id']}")
            print(f"Session ID: {result['session_id']}")
            print(f"Message ID: {result['message_id']}")
            
            # Extract content
            assistant_message = result['response']['choices'][0]['message']['content']
            print(f"Assistant response: {assistant_message}")
        else:
            # Old format
            print(f"Success: {result.get('success', 'N/A')}")
            print(f"User ID: {result.get('user_id', 'N/A')}")
            print(f"Session ID: {result.get('session_id', 'N/A')}")
            print(f"Message: {result.get('message', 'N/A')}")
            
            if 'response' in result and 'choices' in result['response']:
                assistant_message = result['response']['choices'][0]['message']['content']
                print(f"Assistant response: {assistant_message}")
            else:
                print(f"Cannot find assistant message in response: {json.dumps(result, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

# Test streaming chat with stream endpoint
def test_streaming_message():
    url = "http://localhost:8000/api/v1/chat/stream"
    user_id = generate_id()
    session_id = generate_id()
    
    payload = {
        "message": "อธิบายเรื่องดวงดาวในศาสตร์ของไทยให้ฟังหน่อย",
        "user_id": user_id,
        "session_id": session_id
    }
    
    print(f"Testing streaming message endpoint (this will print events as received)...")
    
    with requests.post(url, json=payload, stream=True) as response:
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            for i, line in enumerate(response.iter_lines()):
                if line:
                    # Print each event (limit to first 5 for readability)
                    if i < 5:
                        decoded_line = line.decode('utf-8')
                        print(f"Event: {decoded_line}")
                    elif i == 5:
                        print("... more events (truncated for readability) ...")
        else:
            print(f"Error: {response.text}")

# Test streaming chat with chat endpoint
def test_streaming_chat():
    url = "http://localhost:8000/api/v1/chat"
    user_id = generate_id()
    session_id = generate_id()
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "อธิบายเรื่องดวงดาวในศาสตร์ของไทยให้ฟังหน่อย"
            }
        ],
        "stream": True,
        "user_id": user_id,
        "session_id": session_id
    }
    
    print(f"Testing streaming chat endpoint (this will print events as received)...")
    
    with requests.post(url, json=payload, stream=True) as response:
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            for i, line in enumerate(response.iter_lines()):
                if line:
                    # Print each event (limit to first 5 for readability)
                    if i < 5:
                        decoded_line = line.decode('utf-8')
                        print(f"Event: {decoded_line}")
                    elif i == 5:
                        print("... more events (truncated for readability) ...")
        else:
            print(f"Error: {response.text}")

# Calculate fortune for 14-02-1996 (format as YYYY-MM-DD)
fortune_data = calculate_fortune('1996-02-14')

# Print the result
print(json.dumps(fortune_data, indent=2, ensure_ascii=False))

# Print just the summary
print("\n=== Summary ===")
print(fortune_data["summary"])

# Print top interpretations
print("\n=== Top 3 Individual Interpretations ===")
for interp in fortune_data["individual_interpretations"][:3]:
    print(f"{interp['category']} ({interp['meaning']}): {interp['value']} - {interp['influence']}")

# Print top combinations
print("\n=== Top Combinations ===")
for combo in fortune_data["combination_interpretations"][:2]:
    print(f"{combo['heading']}: {combo['meaning']}")

if __name__ == "__main__":
    print("Testing fortune calculation...")
    test_fortune_calculation()
    
    print("\nTesting fortune explanation...")
    test_fortune_explanation()
    
    print("\nTesting normal chat...")
    test_normal_chat()
    
    print("\nTesting fortune chat...")
    test_fortune_chat()
    
    print("\nTesting chat message endpoint...")
    test_chat_message()
    
    print("\nTesting streaming message endpoint...")
    test_streaming_message()
    
    print("\nTesting streaming chat endpoint...")
    test_streaming_chat() 