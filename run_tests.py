"""
Test runner for the meal prep agent.
"""

import subprocess
import sys


def run_tests():
    """Run all tests and report results."""
    print("🧪 Running Meal Prep Agent Test Suite")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            "poetry", "run", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "-x"  # Stop on first failure
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_unit_tests_only():
    """Run only unit tests (fast tests)."""
    print("🏃‍♂️ Running Unit Tests Only...")
    
    try:
        result = subprocess.run([
            "poetry", "run", "pytest", 
            "tests/", 
            "-v",
            "-m", "not slow and not integration"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--unit":
        success = run_unit_tests_only()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)