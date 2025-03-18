#!/usr/bin/env python
# run_all_tests.py
"""
Master script to run all test scripts for the topic identification and meaning extraction system
"""
import os
import sys
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("system_test_results.log")
    ]
)
logger = logging.getLogger("run_all_tests")

# List of test scripts to run
TEST_SCRIPTS = [
    "test_ai_topic_identification.py",
    "test_meaning_extraction.py",
    "test_birth_chart.py"
]

def run_test(script_name):
    """Run a test script and return whether it succeeded"""
    logger.info(f"Running {script_name}...")
    
    start_time = time.time()
    try:
        # Use PowerShell to run the Python script
        result = subprocess.run(
            ["powershell", f"python {script_name}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check if the script ran successfully
        if result.returncode == 0:
            logger.info(f"[PASS] {script_name} completed successfully in {duration:.2f} seconds")
            return True
        else:
            logger.error(f"[FAIL] {script_name} failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"[ERROR] Error running {script_name}: {str(e)}")
        return False

def main():
    """Run all test scripts and report results"""
    logger.info("=== Starting System-wide Test Suite ===")
    logger.info(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Running {len(TEST_SCRIPTS)} test scripts")
    
    results = {}
    all_success = True
    
    for script in TEST_SCRIPTS:
        script_success = run_test(script)
        results[script] = script_success
        
        if not script_success:
            all_success = False
    
    # Report summary
    logger.info("\n=== Test Suite Results ===")
    for script, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        logger.info(f"{status} - {script}")
    
    if all_success:
        logger.info("\n[SUCCESS] ALL TESTS PASSED - System is functioning correctly")
        print("\n[SUCCESS] ALL TESTS PASSED - System is functioning correctly")
    else:
        failure_count = sum(1 for success in results.values() if not success)
        logger.error(f"\n[FAILURE] {failure_count} TESTS FAILED - System needs attention")
        print(f"\n[FAILURE] {failure_count} TESTS FAILED - System needs attention")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Error in main test runner: {str(e)}", exc_info=True)
        print(f"Error in main test runner: {str(e)}")
        sys.exit(1) 