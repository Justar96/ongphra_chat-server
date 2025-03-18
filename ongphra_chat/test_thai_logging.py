#!/usr/bin/env python
# test_thai_logging.py - Test Thai character logging
from app.core.logging import get_logger
from app.services.session_service import get_session_manager
from datetime import datetime

# Setup logging and get a logger
logger = get_logger("test_thai_logging")

# Log a message with Thai characters
logger.info("Testing Thai character logging: อาทิตย์ (Sunday)")

# Test the session manager
session_manager = get_session_manager()
test_user_id = "test-user-123"
birth_date = datetime(2000, 1, 1)
session_manager.save_birth_info(test_user_id, birth_date, "อาทิตย์")

print("Test completed. Check the logs for Thai characters.") 