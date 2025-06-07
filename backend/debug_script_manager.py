#!/usr/bin/env python3
"""
Debug Script Manager

Simple script to test if the script manager can be imported and run
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_script_manager_import():
    """Test if script manager can be imported"""
    try:
        print("Testing script manager import...")
        from script_manager import script_manager
        print("✅ Script manager imported successfully")
        return script_manager
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Other error: {e}")
        return None

def test_process_modules():
    """Test if process modules can be imported"""
    modules = [
        'process_modules.trade_sync',
        'process_modules.level_monitor',
        'process_modules.price_updater',
        'process_modules.notification_checker',
        'process_modules.position_sync',
        'process_modules.dashboard_sync'
    ]
    
    results = {}
    for module_name in modules:
        try:
            print(f"Testing {module_name}...")
            __import__(module_name)
            print(f"✅ {module_name} imported successfully")
            results[module_name] = True
        except Exception as e:
            print(f"❌ {module_name} failed: {e}")
            results[module_name] = False
    
    return results

def main():
    """Main debug function"""
    print("🔍 Script Manager Debug Tool")
    print("=" * 50)
    
    # Test script manager import
    script_manager = test_script_manager_import()
    
    print("\n" + "=" * 50)
    
    # Test process modules
    module_results = test_process_modules()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if script_manager:
        print("✅ Script Manager: OK")
        try:
            status = script_manager.get_status()
            print(f"✅ Status method: OK ({len(status)} processes)")
        except Exception as e:
            print(f"❌ Status method failed: {e}")
    else:
        print("❌ Script Manager: FAILED")
    
    successful_modules = sum(1 for success in module_results.values() if success)
    total_modules = len(module_results)
    print(f"📦 Process Modules: {successful_modules}/{total_modules} successful")
    
    for module, success in module_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {module}")

if __name__ == "__main__":
    main() 