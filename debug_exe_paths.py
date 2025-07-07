#!/usr/bin/env python3
"""
Debug script to test EXE path handling
"""

import os
import sys

def debug_exe_paths():
    """Debug path information for EXE mode"""
    print("=== EXE Path Debug ===")
    print(f"sys.executable = {sys.executable}")
    print(f"sys._MEIPASS = {getattr(sys, '_MEIPASS', 'Not set')}")
    print(f"Current working directory = {os.getcwd()}")
    print(f"Script directory = {os.path.dirname(os.path.abspath(__file__))}")
    
    # Test different path strategies
    print("\n--- Path Strategy Tests ---")
    
    # Strategy 1: Current get_models_directory()
    if hasattr(sys, '_MEIPASS'):
        exe_dir = os.path.dirname(sys.executable)
        models_dir_1 = os.path.join(exe_dir, 'models')
    else:
        base_path = os.path.abspath('.')
        models_dir_1 = os.path.join(base_path, 'models')
    print(f"Strategy 1 (current): {models_dir_1}")
    print(f"  Exists: {os.path.exists(models_dir_1)}")
    
    # Strategy 2: Always use executable directory
    exe_dir = os.path.dirname(sys.executable)
    models_dir_2 = os.path.join(exe_dir, 'models')
    print(f"Strategy 2 (exe dir): {models_dir_2}")
    print(f"  Exists: {os.path.exists(models_dir_2)}")
    
    # Strategy 3: Use working directory
    models_dir_3 = os.path.join(os.getcwd(), 'models')
    print(f"Strategy 3 (cwd): {models_dir_3}")
    print(f"  Exists: {os.path.exists(models_dir_3)}")
    
    # Strategy 4: Use script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir_4 = os.path.join(script_dir, 'models')
    print(f"Strategy 4 (script dir): {models_dir_4}")
    print(f"  Exists: {os.path.exists(models_dir_4)}")
    
    print("\n--- Testing with _MEIPASS simulation ---")
    # Simulate EXE mode
    original_meipass = getattr(sys, '_MEIPASS', None)
    sys._MEIPASS = "/temp/pyinstaller"
    
    if hasattr(sys, '_MEIPASS'):
        exe_dir = os.path.dirname(sys.executable)
        models_dir_sim = os.path.join(exe_dir, 'models')
    else:
        base_path = os.path.abspath('.')
        models_dir_sim = os.path.join(base_path, 'models')
    print(f"Simulated EXE mode: {models_dir_sim}")
    
    # Restore original
    if original_meipass is None:
        delattr(sys, '_MEIPASS')
    else:
        sys._MEIPASS = original_meipass

if __name__ == "__main__":
    debug_exe_paths() 