#!/usr/bin/env python3
"""
Test script to verify download path handling works correctly
"""

import os
import sys

def get_models_directory():
    """Get the correct models directory path for both Python and EXE modes"""
    # For EXE mode, we need to look in the same directory as the EXE
    if hasattr(sys, '_MEIPASS'):
        # In EXE mode, look for models in the same directory as the EXE
        exe_dir = os.path.dirname(sys.executable)
        models_dir = os.path.join(exe_dir, 'models')
    else:
        # In Python mode, look for models relative to the script
        base_path = os.path.abspath('.')
        models_dir = os.path.join(base_path, 'models')
    
    return models_dir

def test_download_path():
    """Test the download path logic"""
    print("=== Download Path Test ===")
    
    # Test different model types
    test_models = [
        "tts_models/en/vctk/vits",
        "tts_models/en/ljspeech/vits",
        "tts_models/en/ljspeech/tacotron2-DDC"
    ]
    
    models_dir = get_models_directory()
    print(f"Models directory: {models_dir}")
    
    for model_id in test_models:
        folder_name = model_id.split('/')[-1]
        if 'vctk' in model_id:
            folder_name = 'vctk'
        elif 'vits' in model_id:
            folder_name = 'vits'
        elif 'tacotron2' in model_id:
            folder_name = 'tacotron2'
        
        model_folder = os.path.join(models_dir, folder_name)
        print(f"Model ID: {model_id}")
        print(f"  Folder name: {folder_name}")
        print(f"  Download path: {model_folder}")
        print()

if __name__ == "__main__":
    test_download_path()
    print("=== Test Complete ===") 