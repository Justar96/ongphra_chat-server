import logging
import sys
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_startup.log", mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting test script")

try:
    logger.info("Importing app from main")
    from app.main import app
    logger.info("Application imported successfully!")
    print("SUCCESS: Application loaded without errors")
    
    # Write success to a file for easy checking
    with open("logs/startup_result.txt", "w") as f:
        f.write("SUCCESS: Application loaded without errors\n")
except Exception as e:
    error_msg = f"ERROR: {str(e)}"
    logger.error(f"Error importing application: {str(e)}", exc_info=True)
    print(error_msg)
    
    # Write error to a file for easy checking
    with open("logs/startup_result.txt", "w") as f:
        f.write(f"{error_msg}\n")
    
    sys.exit(1) 