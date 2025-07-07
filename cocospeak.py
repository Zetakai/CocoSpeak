import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import numpy as np
import sounddevice as sd
import glob
import json
import threading
from TTS.utils.manage import ModelManager
import itertools
from TTS.utils.synthesizer import Synthesizer  # Always import at top level

# Check Python version
if sys.version_info < (3, 6):
    print("❌ Python 3.6 or higher is required!")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Set environment variables for TTS backend
# Note: Individual models may override this with their own phonemizer settings
os.environ["TTS_BACKEND"] = "gruut"
os.environ["GRUUT_LANG"] = "en"

# Import TTS with proper error handling
try:
    from TTS.utils.synthesizer import Synthesizer
    print("✓ TTS imported successfully")
except ImportError as e:
    print(f"❌ Failed to import TTS: {e}")
    print("Please install TTS: pip install TTS")
except Exception as e:
    print(f"❌ Unexpected error importing TTS: {e}")

# Add this at the top after imports
if hasattr(sys, '_MEIPASS'):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.abspath('.')

def get_models_directory():
    """Get the correct models directory path for both Python and EXE modes"""
    if getattr(sys, 'frozen', False):
        # Running as EXE (PyInstaller sets sys.frozen)
        exe_dir = os.path.dirname(sys.executable)
        models_dir = os.path.join(exe_dir, 'models')
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, 'models')
    return models_dir

def debug_path_info():
    """Debug function to print path information"""
    print(f"DEBUG: sys._MEIPASS = {getattr(sys, '_MEIPASS', 'Not set')}")
    print(f"DEBUG: BASE_PATH = {BASE_PATH}")
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

def get_model_type_from_config(config_path):
    """Determine model type from config file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check for model type indicators
        if 'model' in config:
            model_name = config['model'].lower()
            if 'vits' in model_name:
                return 'VITS'
            elif 'tacotron' in model_name:
                return 'Tacotron2'
            elif 'fastpitch' in model_name:
                return 'FastPitch'
            elif 'glow' in model_name:
                return 'GlowTTS'
        
        # Check for architecture hints
        if 'model_args' in config:
            model_args = config['model_args']
            if 'model' in model_args:
                model_name = model_args['model'].lower()
                if 'vits' in model_name:
                    return 'VITS'
                elif 'tacotron' in model_name:
                    return 'Tacotron2'
                elif 'fastpitch' in model_name:
                    return 'FastPitch'
                elif 'glow' in model_name:
                    return 'GlowTTS'
        
        # Default based on filename
        config_name = os.path.basename(config_path).lower()
        if 'vits' in config_name:
            return 'VITS'
        elif 'tacotron' in config_name:
            return 'Tacotron2'
        elif 'fastpitch' in config_name:
            return 'FastPitch'
        elif 'glow' in config_name:
            return 'GlowTTS'
        
        return 'Unknown'
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return 'Unknown'
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file {config_path}: {e}")
        return 'Unknown'
    except Exception as e:
        print(f"Error reading config file {config_path}: {e}")
        return 'Unknown'

def get_model_size_mb(model_path):
    try:
        size = os.path.getsize(model_path)
        return size / (1024 * 1024)
    except FileNotFoundError:
        print(f"Model file not found: {model_path}")
        return None
    except OSError as e:
        print(f"Error accessing model file {model_path}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting model size for {model_path}: {e}")
        return None

def find_config_file(folder_path, base_name):
    """Helper function to find config file with multiple fallback names"""
    config_candidates = [
        os.path.join(folder_path, f"{base_name}_config.json"),
        os.path.join(folder_path, "config.json"),
        os.path.join(folder_path, f"{base_name}.json")
    ]
    
    for config_path in config_candidates:
        if os.path.exists(config_path):
            return config_path
    return None

def fix_phonemizer_config(config_path):
    """Fix phonemizer configuration issues in model config files"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check if phonemizer is set to espeak but we're using gruut
        if config.get("phonemizer") == "espeak":
            print(f"⚠️  Model {os.path.basename(config_path)} uses 'espeak' phonemizer, switching to 'gruut'")
            config["phonemizer"] = "gruut"
            
            # Also update phoneme_language if needed
            if config.get("phoneme_language") == "en":
                config["phoneme_language"] = "en-us"
            
            # Write the updated config back
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"✓ Updated phonemizer configuration in {config_path}")
            return True
    except Exception as e:
        print(f"Warning: Could not fix phonemizer config for {config_path}: {e}")
        return False

def is_tts_model_type(model_type):
    """Return True if the model_type is a known TTS model, not a vocoder."""
    if not model_type:
        return False
    tts_types = ["vits", "tacotron", "fastpitch", "glow", "tacotron2", "capacitron"]
    vocoder_types = ["hifigan", "melgan", "vocoder"]
    model_type = model_type.lower()
    if any(v in model_type for v in vocoder_types):
        return False
    return any(t in model_type for t in tts_types)

def scan_available_models():
    """Recursively scan models directory for available models organized by type"""
    models = {}
    models_dir = get_models_directory()
    
    print(f"Scanning for models in: {models_dir}")
    
    if not os.path.exists(models_dir):
        print(f"Models directory does not exist: {models_dir}")
        return models
    
    # Fix for Windows: use individual patterns instead of brace expansion
    model_files = []
    for ext in ["pth", "pt", "ckpt", "safetensors"]:
        pattern = os.path.join(models_dir, "**", f"*.{ext}")
        found_files = glob.glob(pattern, recursive=True)
        model_files.extend(found_files)
        print(f"Found {len(found_files)} files with extension .{ext}")
    
    print(f"Total model files found: {len(model_files)}")
    
    for model_file in model_files:
        folder_path = os.path.dirname(model_file)
        model_name = os.path.basename(model_file)
        base_name = model_name.replace("_model.pth", "").replace("_model.pt", "").replace("_model.ckpt", "").replace("_model.safetensors", "").replace(".pth", "").replace(".pt", "").replace(".ckpt", "").replace(".safetensors", "")
        config_file = find_config_file(folder_path, base_name)
        if config_file:
            # Fix phonemizer configuration if needed
            fix_phonemizer_config(config_file)
            model_type = get_model_type_from_config(config_file)
            if not is_tts_model_type(model_type):
                print(f"Skipping vocoder model: {model_name}")
                continue  # skip vocoders
            folder = os.path.basename(folder_path)
            parent_folder = os.path.basename(os.path.dirname(folder_path))
            if folder.lower() == "vctk":
                display_name = f"VITS (VCTK) - Multi-Speaker"
            elif folder.lower() == "vits":
                display_name = f"VITS (LJSpeech) - Single Speaker"
            elif folder.lower() == "custom":
                display_name = f"Custom Model - {model_name}"
            elif parent_folder.lower() == "custom":
                display_name = f"Custom Model - {folder} [{model_name}]"
            else:
                display_name = f"{model_type} - {folder} [{model_name}]"
            size_mb = get_model_size_mb(model_file)
            size_str = f" [{size_mb:.1f} MB]" if size_mb else ""
            models[display_name + size_str] = {
                "model_path": model_file,
                "config_path": config_file,
                "model_type": model_type,
                "folder": folder,
                "description": f"{model_type} model in {folder_path} [{model_name}]{size_str}"
            }
            print(f"Added model: {display_name + size_str}")
        else:
            print(f"No config file found for model: {model_name}")
    
    print(f"Total TTS models found: {len(models)}")
    return models

# Initialize with empty models - will be populated when app starts
MODEL_CONFIGS = {}
DEFAULT_MODEL = "No models found"

# Speaker mapping for VCTK
VCTK_SPEAKER_MAP = {
    "p225": 1, "p226": 2, "p227": 3, "p228": 4, "p229": 5, "p230": 6, "p231": 7, "p232": 8, "p233": 9, "p234": 10, "p236": 11, "p237": 12, "p238": 13, "p239": 14, "p240": 15, "p241": 16, "p243": 17, "p244": 18, "p245": 19, "p246": 20, "p247": 21, "p248": 22, "p249": 23, "p250": 24, "p251": 25, "p252": 26, "p253": 27, "p254": 28, "p255": 29, "p256": 30, "p257": 31, "p258": 32, "p259": 33, "p260": 34, "p261": 35, "p262": 36, "p263": 37, "p264": 38, "p265": 39, "p266": 40, "p267": 41, "p268": 42, "p269": 43, "p270": 44, "p271": 45, "p272": 46, "p273": 47, "p274": 48, "p275": 49, "p276": 50, "p277": 51, "p278": 52, "p279": 53, "p280": 54, "p281": 55, "p282": 56, "p283": 57, "p284": 58, "p285": 59, "p286": 60, "p287": 61, "p288": 62, "p292": 63, "p293": 64, "p294": 65, "p295": 66, "p297": 67, "p298": 68, "p299": 69, "p300": 70, "p301": 71, "p302": 72, "p303": 73, "p304": 74, "p305": 75, "p306": 76, "p307": 77, "p308": 78, "p310": 79, "p311": 80, "p312": 81, "p313": 82, "p314": 83, "p316": 84, "p317": 85, "p318": 86, "p323": 87, "p326": 88, "p329": 89, "p330": 90, "p333": 91, "p334": 92, "p335": 93, "p336": 94, "p339": 95, "p340": 96, "p341": 97, "p343": 98, "p345": 99, "p347": 100, "p351": 101, "p360": 102, "p361": 103, "p362": 104, "p363": 105, "p364": 106, "p374": 107, "p376": 108
}
VCTK_SPEAKERS = list(VCTK_SPEAKER_MAP.keys())

# --- TTS Functions ---
def tts_to_wav(synth, text):
    if synth is None:
        raise Exception("Model not loaded. Please load the model first.")
    wav = synth.tts(text)
    wav = np.array(wav)
    
    # Improve audio clarity
    wav = improve_audio_clarity(wav)
    
    return wav

def improve_audio_clarity(wav):
    """Improve audio clarity by normalizing and filtering"""
    try:
        # Normalize audio to prevent clipping
        wav = wav / np.max(np.abs(wav)) * 0.95
        
        # Apply a gentle high-pass filter to reduce low-frequency noise
        from scipy import signal
        
        # Design a high-pass filter to remove low-frequency noise
        nyquist = 22050 / 2
        cutoff = 80  # Hz - removes very low frequency noise
        b, a = signal.butter(4, cutoff / nyquist, btype='high')
        wav = signal.filtfilt(b, a, wav)
        
        # Apply a gentle low-pass filter to reduce high-frequency artifacts
        cutoff_high = 8000  # Hz - removes very high frequency noise
        b, a = signal.butter(4, cutoff_high / nyquist, btype='low')
        wav = signal.filtfilt(b, a, wav)
        
        # Normalize again after filtering
        wav = wav / np.max(np.abs(wav)) * 0.95
        
        return wav
        
    except ImportError:
        print("Warning: scipy not available, using original audio")
        return wav
    except Exception as e:
        print(f"Warning: Audio clarity improvement failed: {e}")
        return wav





def tts_to_wav_multi_speaker(synth, text, speaker_id):
    """Synthesize speech for multi-speaker models"""
    if synth is None:
        raise Exception("Model not loaded. Please load the model first.")
    
    # For VCTK models, we need to use the speaker parameter
    try:
        # Try with speaker parameter (most common for VCTK)
        wav = synth.tts(text, speaker=speaker_id)
    except Exception as e:
        try:
            # Try speaker_id parameter
            wav = synth.tts(text, speaker_id=speaker_id)
        except Exception as e2:
            try:
                # Try speaker_name parameter
                wav = synth.tts(text, speaker_name=str(speaker_id))
            except Exception as e3:
                # Try as positional argument
                wav = synth.tts(text, speaker_id)
    
    return np.array(wav)

def tts_to_wav_vctk(synth, text, speaker_name):
    if synth is None:
        raise Exception("Model not loaded. Please load the model first.")
    speaker_idx = VCTK_SPEAKER_MAP.get(speaker_name)
    if speaker_idx is None:
        raise Exception(f"Unknown speaker: {speaker_name}")
    zero_based_idx = speaker_idx - 1
    errors = []
    try:
        return np.array(synth.tts(text, speaker_idx=zero_based_idx))
    except Exception as e1:
        errors.append(f"speaker_idx: {e1}")
    try:
        return np.array(synth.tts(text, speaker_id=zero_based_idx))
    except Exception as e2:
        errors.append(f"speaker_id: {e2}")
    try:
        return np.array(synth.tts(text, speaker_idx=zero_based_idx, speaker_id=zero_based_idx))
    except Exception as e3:
        errors.append(f"both: {e3}")
    try:
        return np.array(synth.tts(text, zero_based_idx))
    except Exception as e4:
        errors.append(f"positional: {e4}")
    raise Exception("All attempts failed: " + " | ".join(errors))

def play_audio(wav, sample_rate=22050):
    try:
        # Stop any currently playing audio first
        sd.stop()
        # Small delay to ensure previous audio is fully stopped
        import time
        time.sleep(0.1)
        
        # Ensure audio is in the correct format and range
        wav = np.asarray(wav, dtype=np.float32)
        wav = np.clip(wav, -1.0, 1.0)
        
        # Play new audio with better settings
        sd.play(wav, samplerate=sample_rate, blocking=True)
        
    except Exception as e:
        print(f"Audio playback error: {e}")
        # Try to recover by stopping and waiting
        try:
            sd.stop()
            time.sleep(0.2)
        except:
            pass

def save_wav(wav, sample_rate, file_path):
    try:
        from scipy.io.wavfile import write
        # Ensure wav is in the correct format
        if wav.dtype != np.float32 and wav.dtype != np.float64:
            wav = wav.astype(np.float32)
        
        # Normalize and convert to int16
        wav_normalized = np.clip(wav, -1.0, 1.0)
        wav_int16 = (wav_normalized * 32767).astype(np.int16)
        
        write(file_path, sample_rate, wav_int16)
    except ImportError:
        raise Exception("scipy is required for saving WAV files. Install with: pip install scipy")
    except OSError as e:
        raise Exception(f"Cannot write to file {file_path}: {e}")
    except Exception as e:
        raise Exception(f"Error saving WAV file: {e}")

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CocoSpeak TTS App")
        self.sample_rate = 22050
        self.wav = None
        self.synth = None
        self.loading_anim = None
        self._speaking = False  # Initialize speaking flag
        self._loading_model = False
        self._loading_running = False
        self.loading_label = tk.Label(root, text="", fg="blue")
        self.loading_label.pack()
        
        # Debug path information
        debug_path_info()
        
        # Initialize models - scan for available models
        self.model_configs = scan_available_models()
        if self.model_configs:
            self.current_model = list(self.model_configs.keys())[0]
        else:
            self.current_model = "No models found"

        # Model Selection Frame
        self.model_frame = tk.Frame(root)
        self.model_frame.pack(pady=5)
        
        tk.Label(self.model_frame, text="Select Model:").pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar(value=self.current_model)
        self.model_combo = ttk.Combobox(
            self.model_frame, 
            textvariable=self.model_var,
            values=list(self.model_configs.keys()),
            state="readonly",
            width=30
        )
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        
        # Model Description
        self.desc_label = tk.Label(self.model_frame, text="No models found")
        if self.model_configs and self.current_model in self.model_configs:
            self.desc_label.config(text=self.model_configs[self.current_model]["description"])
        self.desc_label.pack(side=tk.LEFT, padx=10)

        # Refresh Models Button
        self.refresh_button = tk.Button(
            self.model_frame,
            text="🔄 Refresh",
            command=self.refresh_models
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # CUDA/CPU Selection Frame
        self.cuda_frame = tk.Frame(root)
        self.cuda_frame.pack(pady=5)
        
        self.cuda_var = tk.BooleanVar(value=False)
        self.cuda_checkbox = tk.Checkbutton(
            self.cuda_frame, 
            text="Use CUDA (GPU)", 
            variable=self.cuda_var,
            command=self.on_cuda_change
        )
        self.cuda_checkbox.pack(side=tk.LEFT)
        
        self.load_button = tk.Button(
            self.cuda_frame, 
            text="Load Model", 
            command=self.load_model
        )
        self.load_button.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(self.cuda_frame, text="Model not loaded")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Download Model Button
        self.download_button = tk.Button(
            self.cuda_frame,
            text="Download Model",
            command=self.download_model
        )
        self.download_button.pack(side=tk.LEFT, padx=10)

        # Download Online Model Button
        self.download_online_button = tk.Button(
            self.cuda_frame,
            text="Download Online Model",
            command=self.open_online_model_dialog
        )
        self.download_online_button.pack(side=tk.LEFT, padx=10)

        # Import Custom Model Button
        self.import_custom_button = tk.Button(
            self.cuda_frame,
            text="Import Custom Model",
            command=self.import_custom_model
        )
        self.import_custom_button.pack(side=tk.LEFT, padx=10)

        # Speaker Selection Frame (for multi-speaker models)
        self.speaker_frame = tk.Frame(root)
        self.speaker_frame.pack(pady=5)
        
        self.speaker_label = tk.Label(self.speaker_frame, text="Speaker:")
        self.speaker_label.pack(side=tk.LEFT)
        
        self.speaker_var = tk.StringVar(value="p225")
        self.speaker_combo = ttk.Combobox(
            self.speaker_frame,
            textvariable=self.speaker_var,
            values=[],  # Will be set dynamically
            state="readonly",
            width=10
        )
        self.speaker_combo.pack(side=tk.LEFT, padx=5)
        
        # Hide speaker selection initially
        self.speaker_frame.pack_forget()

        # Text Input Frame
        self.text_label = tk.Label(root, text="Enter text:")
        self.text_label.pack()
        self.text_entry = tk.Text(root, height=5, width=50)
        self.text_entry.pack()



        # Control Buttons Frame
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)

        self.speak_button = tk.Button(
            self.button_frame, 
            text="Speak", 
            command=self.speak,
            state=tk.DISABLED
        )
        self.speak_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(
            self.button_frame, 
            text="Save as WAV", 
            command=self.save_wav_file, 
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=5)



    def refresh_models(self):
        """Refresh the model list"""
        print("Refreshing models...")
        
        # Clear current models first
        self.model_configs = {}
        self.model_combo['values'] = []
        self.model_var.set("")
        self.current_model = ""
        self.desc_label.config(text="Scanning for models...")
        self.root.update()
        
        # Scan for models
        self.model_configs = scan_available_models()
        model_names = list(self.model_configs.keys())
        
        print(f"Refresh complete. Found {len(model_names)} models.")
        
        # Update combobox
        self.model_combo['values'] = model_names
        
        if model_names:
            self.model_var.set(model_names[0])
            self.current_model = model_names[0]
            self.desc_label.config(text=self.model_configs[model_names[0]]["description"])
        else:
            self.model_var.set("")
            self.current_model = ""
            self.desc_label.config(text="No models found")
        
        # Reset model
        if self.synth is not None:
            self.synth = None
            self.status_label.config(text="Model not loaded")
            self.speak_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
        
        # Show results
        if model_names:
            messagebox.showinfo("Refresh Complete", f"Found {len(model_names)} model(s)")
        else:
            models_dir = get_models_directory()
            messagebox.showinfo("Refresh Complete", f"No models found.\n\nPlease add models to:\n{models_dir}")

    def on_model_change(self, event=None):
        """Handle model selection change"""
        self.current_model = self.model_var.get()
        if self.current_model in self.model_configs:
            self.desc_label.config(text=self.model_configs[self.current_model]["description"])
            
            # Show/hide speaker selection based on model type
            if "VCTK" in self.current_model or "Multi-Speaker" in self.current_model:
                self.speaker_combo['values'] = VCTK_SPEAKERS
                self.speaker_var.set(VCTK_SPEAKERS[0])
                self.speaker_frame.pack(pady=5)
                self.speaker_label.config(text="Speaker:")
            else:
                self.speaker_frame.pack_forget()
        
        # Reset model when changing selection
        if self.synth is not None:
            self.synth = None
            self.status_label.config(text="Model not loaded")
            self.speak_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)

    def on_cuda_change(self):
        # Reset model when CUDA setting changes
        if self.synth is not None:
            self.synth = None
            self.status_label.config(text="Model not loaded")
            self.speak_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)

    def download_model(self):
        """Open download script"""
        try:
            import subprocess
            subprocess.Popen(["python", "download_specific_model.py"])
            messagebox.showinfo("Download", "Download script opened. Please download the model you want to use.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open download script: {e}")

    def create_download_dialog(self, model_id, model_name):
        """Create a beautiful download dialog with progress bar and cancel option"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Downloading Model")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")
        
        # Style the dialog
        dialog.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = tk.Frame(dialog, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Downloading Model", 
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=(0, 10))
        
        # Model info
        model_info = tk.Label(
            main_frame,
            text=f"Model: {model_name}",
            font=('Arial', 10),
            bg='#f0f0f0',
            fg='#666666'
        )
        model_info.pack(pady=(0, 20))
        
        # Progress frame
        progress_frame = tk.Frame(main_frame, bg='#f0f0f0')
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        progress_bar.pack(pady=(0, 10))
        
        # Progress text
        progress_text = tk.Label(
            progress_frame,
            text="Preparing download...",
            font=('Arial', 9),
            bg='#f0f0f0',
            fg='#666666'
        )
        progress_text.pack()
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#f0f0f0')
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status label
        status_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 9),
            bg='#f0f0f0',
            fg='#666666',
            wraplength=450
        )
        status_label.pack()
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=lambda: self.cancel_download_immediate(dialog),
            bg='#ff6b6b',
            fg='white',
            font=('Arial', 10),
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Variables for download control
        dialog.download_cancelled = False
        dialog.progress_var = progress_var
        dialog.progress_text = progress_text
        dialog.status_label = status_label
        dialog.cancel_button = cancel_button
        
        return dialog

    def cancel_download_immediate(self, dialog):
        """Cancel the download and close the dialog immediately."""
        dialog.download_cancelled = True
        dialog.status_label.config(text="Download canceled.")
        dialog.progress_text.config(text="Canceled.")
        dialog.cancel_button.config(state=tk.DISABLED)
        dialog.after(500, dialog.destroy)

    def download_with_progress(self, model_id, model_name):
        dialog = self.create_download_dialog(model_id, model_name)
        
        def download_thread():
            try:
                import requests
                import tempfile
                import zipfile
                from urllib.parse import urljoin
                import shutil
                manager = ModelManager()
                
                # Update progress for model info fetch
                dialog.progress_var.set(5)
                dialog.progress_text.config(text="Fetching model information...")
                dialog.status_label.config(text="Getting model details from Coqui Hub...")
                dialog.update()
                
                if dialog.download_cancelled:
                    return
                
                # Get model info first
                try:
                    model_info = manager.download_model(model_id)
                    model_path, config_path, model_details = model_info
                except Exception as e:
                    dialog.progress_var.set(10)
                    dialog.progress_text.config(text="Preparing manual download...")
                    dialog.status_label.config(text="Setting up download...")
                    dialog.update()
                    if dialog.download_cancelled:
                        return
                    temp_dir = tempfile.mkdtemp()
                    model_url = f"https://huggingface.co/coqui/{model_id}/resolve/main/model.pth"
                    config_url = f"https://huggingface.co/coqui/{model_id}/resolve/main/config.json"
                    # Download model file
                    dialog.progress_var.set(15)
                    dialog.progress_text.config(text="Downloading model file...")
                    dialog.status_label.config(text="Downloading model weights...")
                    dialog.update()
                    if dialog.download_cancelled:
                        return
                    try:
                        with requests.get(model_url, stream=True, timeout=10) as response:
                            response.raise_for_status()
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            model_path = os.path.join(temp_dir, "model.pth")
                            with open(model_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if dialog.download_cancelled:
                                        dialog.progress_text.config(text="Canceled.")
                                        dialog.status_label.config(text="Download canceled.")
                                        dialog.cancel_button.config(state=tk.DISABLED)
                                        dialog.update()
                                        return
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size > 0:
                                            progress = 15 + (downloaded / total_size) * 60
                                            dialog.progress_var.set(progress)
                                            dialog.progress_text.config(text=f"Downloading model... {progress:.1f}%")
                                            dialog.status_label.config(text=f"Downloaded {downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB")
                                            dialog.update()
                    except Exception as e:
                        if dialog.download_cancelled:
                            return
                        dialog.progress_text.config(text="Download failed!")
                        dialog.status_label.config(text=f"Error downloading model: {str(e)}")
                        dialog.cancel_button.config(text="Close", command=dialog.destroy)
                        dialog.update()
                        messagebox.showerror("Download Error", f"Failed to download model file: {e}")
                        return
                    # Download config file
                    dialog.progress_var.set(75)
                    dialog.progress_text.config(text="Downloading config file...")
                    dialog.status_label.config(text="Downloading model configuration...")
                    dialog.update()
                    if dialog.download_cancelled:
                        return
                    try:
                        with requests.get(config_url, stream=True, timeout=10) as response:
                            response.raise_for_status()
                            config_path = os.path.join(temp_dir, "config.json")
                            with open(config_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if dialog.download_cancelled:
                                        dialog.progress_text.config(text="Canceled.")
                                        dialog.status_label.config(text="Download canceled.")
                                        dialog.cancel_button.config(state=tk.DISABLED)
                                        dialog.update()
                                        return
                                    if chunk:
                                        f.write(chunk)
                            dialog.progress_var.set(85)
                            dialog.progress_text.config(text="Config downloaded!")
                            dialog.status_label.config(text="Configuration file downloaded successfully")
                            dialog.update()
                    except Exception as e:
                        if dialog.download_cancelled:
                            return
                        dialog.progress_text.config(text="Config download failed!")
                        dialog.status_label.config(text=f"Error downloading config: {str(e)}")
                        dialog.cancel_button.config(text="Close", command=dialog.destroy)
                        dialog.update()
                        messagebox.showerror("Download Error", f"Failed to download config file: {e}")
                        return
                if dialog.download_cancelled:
                    return
                # Organize files
                dialog.progress_var.set(90)
                dialog.progress_text.config(text="Organizing files...")
                dialog.status_label.config(text="Organizing downloaded files...")
                dialog.update()
                folder_name = model_id.split('/')[-1]
                if 'vctk' in model_id:
                    folder_name = 'vctk'
                elif 'vits' in model_id:
                    folder_name = 'vits'
                elif 'tacotron2' in model_id:
                    folder_name = 'tacotron2'
                # Use the correct models directory for downloads
                models_dir = get_models_directory()
                model_folder = os.path.join(models_dir, folder_name)
                print(f"Downloading model to: {model_folder}")
                os.makedirs(model_folder, exist_ok=True)
                local_model_path = os.path.join(model_folder, f"{folder_name}_model.pth")
                local_config_path = os.path.join(model_folder, f"{folder_name}_config.json")
                shutil.copy2(model_path, local_model_path)
                shutil.copy2(config_path, local_config_path)
                if dialog.download_cancelled:
                    return
                dialog.progress_var.set(100)
                dialog.progress_text.config(text="Download complete!")
                dialog.status_label.config(text=f"Model downloaded to {model_folder}/")
                dialog.cancel_button.config(text="Close", command=dialog.destroy)
                dialog.update()
                messagebox.showinfo("Success", f"Model downloaded successfully!\nLocation: {model_folder}/")
            except Exception as e:
                if not getattr(dialog, 'download_cancelled', False):
                    dialog.progress_text.config(text="Download failed!")
                    dialog.status_label.config(text=f"Error: {str(e)}")
                    dialog.cancel_button.config(text="Close", command=dialog.destroy)
                    dialog.update()
                    messagebox.showerror("Download Error", f"Failed to download model: {e}")
        import threading
        download_thread_obj = threading.Thread(target=download_thread, daemon=True)
        download_thread_obj.start()

    def open_online_model_dialog(self):
        def fetch_and_show():
            try:
                self.start_loading("Fetching model list")
                manager = ModelManager()
                model_ids = manager.list_models()
                
                # Filter out vocoder models
                def is_tts_model_id(model_id):
                    tts_keywords = ["vits", "tacotron", "fastpitch", "glow", "tacotron2", "capacitron"]
                    vocoder_keywords = ["hifigan", "melgan", "vocoder"]
                    model_id_lower = model_id.lower()
                    if any(v in model_id_lower for v in vocoder_keywords):
                        return False
                    return any(t in model_id_lower for t in tts_keywords)
                
                filtered_model_ids = [mid for mid in model_ids if is_tts_model_id(mid)]
                
                def parse_model_id(model_id):
                    parts = model_id.split('/')
                    if len(parts) >= 4:
                        return f"{parts[1]} | {parts[2]} | {parts[3]}"
                    return model_id
                
                model_names = [parse_model_id(mid) for mid in filtered_model_ids]
                self.stop_loading()
                
                if not filtered_model_ids:
                    messagebox.showerror("No Models", "No TTS models found in the online model list.")
                    return
                
                # Create beautiful model selection dialog
                dialog = tk.Toplevel(self.root)
                dialog.title("Download TTS Model")
                dialog.geometry("700x500")
                dialog.resizable(False, False)
                dialog.transient(self.root)
                dialog.grab_set()
                
                # Center the dialog
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
                y = (dialog.winfo_screenheight() // 2) - (500 // 2)
                dialog.geometry(f"700x500+{x}+{y}")
                
                # Style the dialog
                dialog.configure(bg='#f0f0f0')
                
                # Main frame
                main_frame = tk.Frame(dialog, bg='#f0f0f0')
                main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                # Title
                title_label = tk.Label(
                    main_frame, 
                    text="Select Model to Download", 
                    font=('Arial', 16, 'bold'),
                    bg='#f0f0f0',
                    fg='#333333'
                )
                title_label.pack(pady=(0, 10))
                
                # Description
                desc_label = tk.Label(
                    main_frame,
                    text="Choose a model from the Coqui TTS Hub to download:",
                    font=('Arial', 10),
                    bg='#f0f0f0',
                    fg='#666666'
                )
                desc_label.pack(pady=(0, 20))
                
                # List frame
                list_frame = tk.Frame(main_frame, bg='#f0f0f0')
                list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
                
                # Create listbox with scrollbar
                listbox_frame = tk.Frame(list_frame, bg='#f0f0f0')
                listbox_frame.pack(fill=tk.BOTH, expand=True)
                
                scrollbar = tk.Scrollbar(listbox_frame)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                listbox = tk.Listbox(
                    listbox_frame, 
                    yscrollcommand=scrollbar.set, 
                    width=80, 
                    height=15,
                    font=('Arial', 9),
                    selectmode=tk.SINGLE,
                    bg='white',
                    fg='#333333',
                    selectbackground='#4a90e2',
                    selectforeground='white'
                )
                listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.config(command=listbox.yview)
                
                # Populate listbox
                for name in model_names:
                    listbox.insert(tk.END, name)
                
                # Status label
                status_label = tk.Label(
                    main_frame, 
                    text="", 
                    font=('Arial', 9),
                    bg='#f0f0f0',
                    fg='#666666',
                    wraplength=650
                )
                status_label.pack(pady=(0, 10))
                
                # Button frame
                button_frame = tk.Frame(main_frame, bg='#f0f0f0')
                button_frame.pack(fill=tk.X)
                
                # Download button
                download_btn = tk.Button(
                    button_frame, 
                    text="Download Selected Model",
                    command=lambda: self.handle_model_download(listbox, filtered_model_ids, model_names, status_label, dialog),
                    bg='#4a90e2',
                    fg='white',
                    font=('Arial', 10, 'bold'),
                    relief=tk.FLAT,
                    padx=20,
                    pady=8
                )
                download_btn.pack(side=tk.RIGHT, padx=(10, 0))
                
                # Close button
                close_btn = tk.Button(
                    button_frame, 
                    text="Close",
                    command=dialog.destroy,
                    bg='#666666',
                    fg='white',
                    font=('Arial', 10),
                    relief=tk.FLAT,
                    padx=20,
                    pady=8
                )
                close_btn.pack(side=tk.RIGHT)
                
            except Exception as e:
                self.stop_loading()
                messagebox.showerror("Error", f"Failed to fetch model list: {e}")
        
        threading.Thread(target=fetch_and_show, daemon=True).start()

    def handle_model_download(self, listbox, model_ids, model_names, status_label, dialog):
        """Handle the model download process"""
        sel = listbox.curselection()
        if not sel:
            status_label.config(text="Please select a model to download.")
            return
        
        idx = sel[0]
        model_id = model_ids[idx]
        model_name = model_names[idx]
        
        # Close the selection dialog
        dialog.destroy()
        
        # Start the download with progress
        self.download_with_progress(model_id, model_name)

    def load_model(self):
        if not self.current_model or self.current_model not in self.model_configs:
            messagebox.showerror("Error", "Please select a valid model first.")
            return
        
        # Prevent multiple simultaneous loads
        if hasattr(self, '_loading_model') and self._loading_model:
            messagebox.showwarning("Already loading", "Please wait for the current model to finish loading.")
            return
        
        def load_model_thread():
            try:
                self._loading_model = True
                use_cuda = self.cuda_var.get()
                model_config = self.model_configs[self.current_model]
                
                # Thread-safe GUI updates
                self.root.after(0, lambda: self.status_label.config(text=f"Loading {self.current_model}..."))
                self.root.after(0, lambda: self.start_loading("Loading model"))
                
                # Check if files exist
                if not os.path.exists(model_config["model_path"]):
                    raise FileNotFoundError(f"Model file not found: {model_config['model_path']}\nPlease download the model first.")
                if not os.path.exists(model_config["config_path"]):
                    raise FileNotFoundError(f"Config file not found: {model_config['config_path']}\nPlease download the model first.")
                
                # Load model with proper configuration
                self.synth = Synthesizer(
                    tts_checkpoint=model_config["model_path"],
                    tts_config_path=model_config["config_path"],
                    use_cuda=use_cuda
                )
                
                # Thread-safe success updates
                self.root.after(0, lambda: self.status_label.config(text=f"{self.current_model} loaded ({'CUDA' if use_cuda else 'CPU'})"))
                self.root.after(0, lambda: self.speak_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: messagebox.showinfo("Success", f"{self.current_model} loaded successfully!"))
                
            except FileNotFoundError as e:
                error_msg = f"Model files not found: {e}\n\nPlease ensure:\n1. Model files exist in models/\n2. Download the model first"
                self.root.after(0, lambda: self.status_label.config(text="Model load failed"))
                self.root.after(0, lambda: messagebox.showerror("Model Load Error", error_msg))
            except ImportError as e:
                error_msg = f"TTS library error: {e}\n\nPlease ensure TTS is properly installed"
                self.root.after(0, lambda: self.status_label.config(text="Model load failed"))
                self.root.after(0, lambda: messagebox.showerror("Import Error", error_msg))
            except Exception as e:
                error_msg = f"Failed to load {self.current_model}: {e}\n\n"
                
                # Check for specific phonemizer errors
                if "phonemizer" in str(e).lower() or "phoneme" in str(e).lower():
                    error_msg += "This appears to be a phonemizer configuration issue.\n"
                    error_msg += "The model may need a different phonemizer setting.\n\n"
                    error_msg += "Try:\n"
                    error_msg += "1. Restart the app to auto-fix phonemizer settings\n"
                    error_msg += "2. Check if gruut/espeak is properly installed\n"
                    error_msg += "3. Try a different model\n"
                else:
                    error_msg += "Please ensure:\n1. Model files exist in models/\n2. Model files are not corrupted\n3. TTS library is properly installed"
                
                self.root.after(0, lambda: self.status_label.config(text="Model load failed"))
                self.root.after(0, lambda: messagebox.showerror("Model Load Error", error_msg))
            finally:
                self._loading_model = False
                self.root.after(0, lambda: self.stop_loading())
        
        import threading
        threading.Thread(target=load_model_thread, daemon=True).start()

    def start_loading(self, msg="Loading"):
        if self.loading_anim:
            return
        self.loading_label.config(text=msg)
        self.loading_label.lift()
        self.loading_label.update()
        self._loading_running = True
        def animate():
            dots = itertools.cycle(["", ".", "..", "..."])
            while self._loading_running:
                self.loading_label.config(text=msg + next(dots))
                self.loading_label.update()
                import time; time.sleep(0.4)
        import threading
        self.loading_anim = threading.Thread(target=animate, daemon=True)
        self.loading_anim.start()

    def stop_loading(self):
        self._loading_running = False
        self.loading_label.config(text="")
        self.loading_anim = None



    def speak(self):
        if self.synth is None:
            messagebox.showwarning("Model not loaded", "Please load the model first.")
            return
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input required", "Please enter some text.")
            return
        
        # Prevent multiple simultaneous synthesis
        if hasattr(self, '_speaking') and self._speaking:
            messagebox.showwarning("Already speaking", "Please wait for the current synthesis to finish.")
            return
        
        def do_speak():
            try:
                self._speaking = True
                # Disable all buttons during synthesis with grey styling
                self.root.after(0, lambda: self.speak_button.config(
                    state=tk.DISABLED, 
                    bg='#e0e0e0', 
                    fg='#666666'
                ))
                self.root.after(0, lambda: self.save_button.config(
                    state=tk.DISABLED, 
                    bg='#e0e0e0', 
                    fg='#666666'
                ))
                self.root.after(0, lambda: self.start_loading("Synthesizing"))
                self.root.after(0, lambda: self.status_label.config(text="Synthesizing speech..."))
                
                if "VCTK" in self.current_model or "Multi-Speaker" in self.current_model:
                    speaker_name = self.speaker_var.get()
                    print(f"Using multi-speaker model with speaker: {speaker_name}")
                    self.wav = tts_to_wav_vctk(self.synth, text, speaker_name)
                else:
                    print(f"Using single-speaker model")
                    self.wav = tts_to_wav(self.synth, text)
                
                # Update status for playback
                self.root.after(0, lambda: self.start_loading("Playing audio..."))
                self.root.after(0, lambda: self.status_label.config(text="Playing audio..."))
                
                # Play audio
                play_audio(self.wav, self.sample_rate)
                
                # Re-enable buttons after completion
                self.root.after(0, lambda: self.speak_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.save_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_label.config(text=f"{self.current_model} ready"))
                
            except Exception as e:
                error_msg = f"Failed to synthesize speech: {e}\n\nModel: {self.current_model}\nText: {text}"
                if "VCTK" in self.current_model or "Multi-Speaker" in self.current_model:
                    error_msg += f"\nSpeaker: {self.speaker_var.get()}"
                self.root.after(0, lambda: messagebox.showerror("Synthesis Error", error_msg))
            finally:
                self._speaking = False
                self.root.after(0, lambda: self.stop_loading())
        
        import threading
        threading.Thread(target=do_speak, daemon=True).start()

    def save_wav_file(self):
        if self.wav is None:
            messagebox.showwarning("No audio", "Please generate speech first.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if file_path:
            try:
                save_wav(self.wav, self.sample_rate, file_path)
                messagebox.showinfo("Saved", f"Audio saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save audio: {e}")

    def import_custom_model(self):
        try:
            model_path = filedialog.askopenfilename(
                title="Select Model File",
                filetypes=[("All Supported Models", "*.pth;*.pt;*.ckpt;*.safetensors"), ("PyTorch Model", "*.pth"), ("PyTorch Checkpoint", "*.pt"), ("Checkpoint", "*.ckpt"), ("SafeTensors", "*.safetensors")]
            )
            if not model_path:
                return
            config_path = filedialog.askopenfilename(
                title="Select Config .json File",
                filetypes=[("Config JSON", "*.json")]
            )
            if not config_path:
                return
            model_name = simpledialog.askstring(
                "Model Name",
                "Enter a name for your custom model (no spaces):",
                parent=self.root
            )
            if not model_name:
                return
            model_name = model_name.replace(" ", "_")
            # Use the correct models directory for imports
            models_dir = get_models_directory()
            dest_folder = os.path.join(models_dir, "custom", model_name)
            print(f"Importing custom model to: {dest_folder}")
            os.makedirs(dest_folder, exist_ok=True)
            dest_model = os.path.join(dest_folder, os.path.basename(model_path))
            dest_config = os.path.join(dest_folder, os.path.basename(config_path))
            import shutil
            shutil.copy2(model_path, dest_model)
            shutil.copy2(config_path, dest_config)
            messagebox.showinfo("Success", f"Custom model imported as '{model_name}'.")
            self.refresh_models()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import custom model: {e}")

    def cleanup(self):
        """Clean up resources before closing"""
        try:
            # Stop any ongoing operations
            self._speaking = False
            self._loading_model = False
            self._loading_running = False
            
            # Stop any audio playback
            try:
                sd.stop()
                import time
                time.sleep(0.2)  # Give audio time to stop
            except Exception as audio_error:
                print(f"Audio cleanup warning: {audio_error}")
            
            # Clear synthesizer to free memory
            if hasattr(self, 'synth') and self.synth is not None:
                self.synth = None
            
            print("✓ Cleanup completed")
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    
    # Set up cleanup on window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop() 