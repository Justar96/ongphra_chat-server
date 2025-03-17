# Thai Fortune Telling Chat Interface

This is a web-based chat interface for testing the Thai Fortune Telling API.

## Features

- Web-based chat interface
- Support for Thai and English languages
- Streaming and non-streaming response options
- Real-time chat with WebSocket communication
- Automatic dependency management
- General questions mode without birth information

## Requirements

- Python 3.8+
- PowerShell 5.0+ (for Windows)

The following Python packages will be installed automatically:
- FastAPI
- Uvicorn[standard] (includes WebSocket support)
- Jinja2
- websockets
- python-multipart
- sse-starlette (for Server-Sent Events)

## Installation

The chat interface will automatically install or upgrade required dependencies when you run it. If you prefer to install dependencies manually:

```bash
cd ongphra_chat
python -m pip install -r chat_requirements.txt
```

## Running the Chat Interface

### Using the Batch File (Windows)

Simply double-click the `run_chat.bat` file or run it from the command line:

```batch
cd ongphra_chat
run_chat.bat [options]
```

The batch file will:
1. Check for PowerShell availability
2. Change to the correct directory
3. Install/upgrade required dependencies
4. Start the chat interface

### Using PowerShell Directly (Windows)

```powershell
cd ongphra_chat
.\run_chat.ps1 [options]
```

### Using Python Directly (Cross-platform)

```bash
cd ongphra_chat
python -m pip install -r chat_requirements.txt  # First time only
python chat_interface.py --host 127.0.0.1 --port 8080 [options]
```

### Command Line Options

- `--host`: Host to bind the server to (default: 127.0.0.1)
- `--port`: Port to bind the server to (default: 8080)
- `--debug`: Enable debug mode

Examples:
```powershell
# Run with default settings
.\run_chat.ps1

# Run on a different port
.\run_chat.ps1 --port 8081

# Run in debug mode
.\run_chat.ps1 --debug

# Run on all interfaces
.\run_chat.ps1 --host 0.0.0.0
```

## Using the Chat Interface

1. Open your web browser and navigate to `http://127.0.0.1:8080` (or your configured host:port)
2. You have two options:
   - **With Birth Information**: Enter your birth date and Thai day, then click "Connect with Birth Info"
   - **General Mode**: Click "General Chat" to ask questions without providing birth information
3. Choose your preferred language (Thai or English)
4. Toggle streaming mode if desired
5. Type your question in the input field and press Enter or click "Send"
6. View the fortune telling response in the chat window

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - The script will automatically install required dependencies
   - If you see dependency errors, try running `python -m pip install -r chat_requirements.txt` manually

2. **WebSocket Connection Failed**
   - Make sure you have `uvicorn[standard]` or `websockets` installed
   - Check that your browser supports WebSocket connections
   - Verify that no firewall is blocking the connection

3. **Script Not Found**
   - Make sure you're running the scripts from the `ongphra_chat` directory
   - Check that all files are in their correct locations

4. **PowerShell Execution Policy**
   - If you get a PowerShell execution policy error, try running PowerShell as administrator and use:
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

### Error Messages

- If you see "No supported WebSocket library detected", the script will automatically install the required packages
- If you get "Address already in use", try using a different port with `--port`
- For other errors, check the console output for detailed error messages

## Notes

- This interface is for testing purposes only
- The chat interface connects to the same backend services as the main API
- All fortune readings are based on the Thai 7 Numbers 9 Bases system

## Recent Updates

- Added general questions mode without requiring birth information
- Added Server-Sent Events for streaming in general mode
- Added automatic dependency installation
- Improved error handling in startup scripts
- Added detailed troubleshooting information
- Updated PowerShell script with better path handling
- Enhanced batch file with error checking
- Added WebSocket support through uvicorn[standard] 