#!/usr/bin/env python3
"""
🎰 BETFIRST CASINO - PRODUCTION EXECUTION
========================================

Direct execution script for Betfirst Casino production review.
Bypasses complex import issues by executing the fixed ccms_pipeline directly.
"""

import subprocess
import sys
import time
from datetime import datetime

def run_betfirst_production():
    """Execute production review for Betfirst Casino"""
    
    print("🎰 BETFIRST CASINO - PRODUCTION EXECUTION")
    print("=" * 50)
    print(f"Casino: Betfirst")
    print(f"Target Words: 2,500")
    print(f"Publisher: crashcasino")
    print(f"Locale: en-US")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    start_time = time.time()
    
    print("\n🚀 Starting production pipeline...")
    print("📊 Command: python ccms_pipeline.py betfirst en-US crashcasino")
    
    try:
        # Execute the production pipeline
        result = subprocess.run([
            "python", "ccms_pipeline.py", 
            "betfirst", "en-US", "crashcasino"
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        duration = time.time() - start_time
        
        print(f"\n📊 EXECUTION RESULTS")
        print("=" * 25)
        print(f"⏱️  Duration: {duration:.1f}s")
        print(f"✅ Return Code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"✅ Status: SUCCESS")
            print(f"📝 Output:")
            print(result.stdout)
        else:
            print(f"❌ Status: FAILED")
            print(f"❌ Error Output:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ Pipeline execution timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return False

if __name__ == "__main__":
    success = run_betfirst_production()
    
    if success:
        print(f"\n🎉 Betfirst production review completed successfully!")
    else:
        print(f"\n💥 Betfirst production review failed!")
        sys.exit(1)