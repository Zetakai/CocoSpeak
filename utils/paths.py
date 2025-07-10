import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def get_models_directory():
    """Get the correct models directory path for both Python and EXE modes"""
    if getattr(sys, 'frozen', False):
        # Running as EXE (PyInstaller sets sys.frozen)
        exe_dir = os.path.dirname(sys.executable)
        models_dir = os.path.join(exe_dir, 'models')
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, '..', 'models')
    return os.path.abspath(models_dir)

def debug_path_info():
    """Debug function to print path information"""
    print(f"DEBUG: sys._MEIPASS = {getattr(sys, '_MEIPASS', 'Not set')}")
    print(f"DEBUG: Models directory = {get_models_directory()}")
    print(f"DEBUG: Models directory exists = {os.path.exists(get_models_directory())}")
    if os.path.exists(get_models_directory()):
        print(f"DEBUG: Models directory contents = {os.listdir(get_models_directory())}")
    
    # Print helpful information for users
    models_dir = get_models_directory()
    print(f"\n📁 Models should be placed in: {models_dir}")
    if not os.path.exists(models_dir):
        print(f"⚠️  Models directory does not exist. Creating it...")
        try:
            os.makedirs(models_dir, exist_ok=True)
            print(f"✓ Created models directory: {models_dir}")
        except Exception as e:
            print(f"❌ Failed to create models directory: {e}")
    else:
        print(f"✓ Models directory exists")
        contents = os.listdir(models_dir)
        if contents:
            print(f"📦 Current contents: {contents}")
        else:
            print(f"📭 Directory is empty")

def ensure_models_directory():
    """Ensure the models directory exists."""
    models_dir = get_models_directory()
    if not os.path.exists(models_dir):
        try:
            os.makedirs(models_dir, exist_ok=True)
            print(f"✓ Created models directory: {models_dir}")
        except Exception as e:
            print(f"❌ Failed to create models directory: {e}")
            return False
    return True 