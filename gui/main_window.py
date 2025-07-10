import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QTextEdit, QPushButton, QCheckBox,
                             QMessageBox, QFileDialog, QProgressBar, QListWidget,
                             QDialog, QLineEdit, QFrame, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence
import keyboard
import threading
import collections
import platform
import json
from tts_module.model_manager import get_available_models
from tts_module.synthesis import load_model, tts_to_wav
from tts_module.audio import play_audio, save_wav, get_default_output_path
from gui.dialogs import OnlineModelDialog, CustomModelImportDialog, HotkeyDialog

class SynthesisThread(QThread):
    """Thread for running synthesis to avoid blocking the UI."""
    finished = pyqtSignal(object)  # Emits the audio data
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, model_path, config_path, text, speaker_id, use_cuda):
        super().__init__()
        self.model_path = model_path
        self.config_path = config_path
        self.text = text
        self.speaker_id = speaker_id
        self.use_cuda = use_cuda
        
    def run(self):
        try:
            # Load model
            synth = load_model(self.model_path, self.config_path, self.use_cuda)
            if synth is None:
                self.error.emit("Failed to load model")
                return
                
            # Synthesize
            wav = tts_to_wav(synth, self.text, self.speaker_id)
            self.finished.emit(wav)
            
        except Exception as e:
            self.error.emit(str(e))

class ModelLoadThread(QThread):
    """Thread for loading models to avoid blocking the UI."""
    finished = pyqtSignal(object)  # Emits the synthesizer
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, model_path, config_path, use_cuda):
        super().__init__()
        self.model_path = model_path
        self.config_path = config_path
        self.use_cuda = use_cuda
        
    def run(self):
        try:
            synth = load_model(self.model_path, self.config_path, self.use_cuda)
            if synth is None:
                self.error.emit("Failed to load model")
                return
            self.finished.emit(synth)
        except Exception as e:
            self.error.emit(str(e))

class HotkeyInputDialog(QDialog):
    """Dialog for capturing hotkey combinations."""
    
    def __init__(self, current_hotkey="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Hotkey")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        self.hotkey = current_hotkey
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Press the key combination you want to use as hotkey:")
        instructions.setFont(QFont("Arial", 10))
        layout.addWidget(instructions)
        
        # Hotkey display
        self.hotkey_label = QLabel(self.hotkey or "No hotkey set")
        self.hotkey_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Match Enter text style (dark bg, border, padding)
        self.hotkey_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                background: #222; /* dark background for dark mode */
                color: #eee;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.hotkey_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Install event filter to capture key combinations
        self.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            # Capture the key combination
            modifiers = []
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                modifiers.append("ctrl")
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                modifiers.append("alt")
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                modifiers.append("shift")
            if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
                modifiers.append("meta")
                
            # Get the key name as string
            if event.text():
                key_name = event.text().lower()
            else:
                key_seq = QKeySequence(event.key())
                key_name = key_seq.toString().lower() if key_seq.toString() else str(event.key())
                
            # Build the hotkey string
            if modifiers:
                self.hotkey = "+".join(modifiers + [key_name])
            else:
                self.hotkey = key_name
                
            self.hotkey_label.setText(self.hotkey)
            return True
            
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CocoSpeak TTS App")
        self.resize(1000, 700)
        self.hotkey = '/'  # Set default hotkey to '/'
        self.sample_rate = 22050
        self.current_audio = None
        self.synth = None
        self._speaking = False
        self._loading_model = False
        self.is_minimized = False
        self.tts_queue = collections.deque()
        self._hotkey_handler = None
        self.queue_lock = threading.Lock() # Add a lock for thread-safe queue access
        
        self.setup_ui()
        self.populate_models()
        self.register_global_hotkey(self.hotkey)
        QTimer.singleShot(100, self.focus_text_entry)

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        
        # Model Selection Frame
        model_group = QGroupBox("Model Selection")
        model_layout = QVBoxLayout()
        
        # Model dropdown and description
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Select Model:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_change)
        model_row.addWidget(self.model_combo)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_models)
        model_row.addWidget(self.refresh_btn)
        
        model_layout.addLayout(model_row)
        
        # Model description
        self.desc_label = QLabel("No models found")
        model_layout.addWidget(self.desc_label)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # CUDA and Model Loading Frame
        cuda_group = QGroupBox("Model Loading")
        cuda_layout = QHBoxLayout()
        cuda_layout.setSpacing(4)  # Lower margin between controls
        # CUDA checkbox
        self.cuda_checkbox = QCheckBox("Use CUDA (GPU)")
        try:
            import torch
            cuda_available = torch.cuda.is_available()
        except:
            cuda_available = False
        self.cuda_checkbox.setChecked(cuda_available)
        self.cuda_checkbox.toggled.connect(self.on_cuda_change)
        cuda_layout.addWidget(self.cuda_checkbox)
        # Button width for all model loading buttons
        btn_width = 170
        # Load model button
        self.load_btn = QPushButton("Load Model")
        self.load_btn.setFixedWidth(btn_width)
        self.load_btn.clicked.connect(self.load_model)
        cuda_layout.addWidget(self.load_btn)
        # Status label (inline, not wide)
        self.status_label = QLabel("Model not loaded")
        cuda_layout.addWidget(self.status_label)
        # Download online model button
        self.download_online_btn = QPushButton("Download Online Model")
        self.download_online_btn.setFixedWidth(btn_width)
        self.download_online_btn.clicked.connect(self.open_online_model_dialog)
        cuda_layout.addWidget(self.download_online_btn)
        # Import custom model button
        self.import_custom_btn = QPushButton("Import Custom Model")
        self.import_custom_btn.setFixedWidth(btn_width)
        self.import_custom_btn.clicked.connect(self.import_custom_model)
        cuda_layout.addWidget(self.import_custom_btn)
        # Hotkey button shows current hotkey
        self.hotkey_btn = QPushButton(f"Set Hotkey ({self.hotkey})")
        self.hotkey_btn.setFixedWidth(170)
        self.hotkey_btn.clicked.connect(self.set_hotkeys)
        cuda_layout.addWidget(self.hotkey_btn)
        cuda_group.setLayout(cuda_layout)
        layout.addWidget(cuda_group)
        
        # Speaker Selection Frame
        self.speaker_group = QGroupBox("Speaker Selection")
        speaker_layout = QHBoxLayout()
        speaker_layout.addWidget(QLabel("Speaker:"))
        self.speaker_combo = QComboBox()
        speaker_layout.addWidget(self.speaker_combo)
        self.speaker_group.setLayout(speaker_layout)
        self.speaker_group.setVisible(False)
        layout.addWidget(self.speaker_group)
        
        # Text and Queue Frame
        text_queue_group = QGroupBox("Text Input and Queue")
        text_queue_layout = QVBoxLayout()
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        
        # Text input on the left
        text_frame = QFrame()
        text_layout = QVBoxLayout()
        text_label = QLabel("Enter text:")
        text_layout.addWidget(text_label)
        self.text_input = QTextEdit()
        self.text_input.setMinimumHeight(120)
        self.text_input.installEventFilter(self)
        text_layout.addWidget(self.text_input)
        text_frame.setLayout(text_layout)
        splitter.addWidget(text_frame)
        
        # Queue on the right
        queue_frame = QFrame()
        queue_layout = QVBoxLayout()
        queue_label = QLabel("TTS Queue:")
        queue_layout.addWidget(queue_label)
        self.queue_listbox = QListWidget()
        self.queue_listbox.setMinimumHeight(120)
        queue_layout.addWidget(self.queue_listbox)
        queue_btn_layout = QHBoxLayout()
        self.remove_queue_btn = QPushButton("Remove Selected")
        self.remove_queue_btn.clicked.connect(self.remove_selected_from_queue)
        queue_btn_layout.addWidget(self.remove_queue_btn)
        self.clear_queue_btn = QPushButton("Clear All")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_btn_layout.addWidget(self.clear_queue_btn)
        queue_layout.addLayout(queue_btn_layout)
        queue_frame.setLayout(queue_layout)
        splitter.addWidget(queue_frame)
        # Set initial sizes to 50/50
        splitter.setSizes([500, 500])
        text_queue_layout.addWidget(splitter)
        text_queue_group.setLayout(text_queue_layout)
        layout.addWidget(text_queue_group)
        
        # Control Buttons Frame
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout()
        
        self.speak_btn = QPushButton("Speak")
        self.speak_btn.clicked.connect(self.queue_speak)
        self.speak_btn.setEnabled(False)
        control_layout.addWidget(self.speak_btn)
        
        self.save_btn = QPushButton("Save as WAV")
        self.save_btn.clicked.connect(self.save_wav_file)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        # Phonemizer selection
        control_layout.addWidget(QLabel("Phonemizer:"))
        self.phonemizer_combo = QComboBox()
        self.phonemizer_combo.addItems(["gruut", "espeak"])
        self.phonemizer_combo.currentTextChanged.connect(self.on_phonemizer_change)
        control_layout.addWidget(self.phonemizer_combo)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Set phonemizer default to espeak
        self.phonemizer_combo.setCurrentText("espeak")
        
    def populate_models(self):
        """Populate the model dropdown with available models."""
        models = get_available_models()
        self.model_combo.clear()
        if not models:
            self.model_combo.addItem("No models found")
        else:
            for model in models:
                self.model_combo.addItem(model["display_name"], model)
                
    def on_model_change(self, text):
        """Handle model selection change."""
        if text == "No models found":
            return
            
        # Get selected model data
        current_data = self.model_combo.currentData()
        if not current_data:
            return
            
        # Update description
        self.desc_label.setText(current_data.get("description", ""))
        
        # Update speaker dropdown
        speakers = current_data.get("speakers_list")
        self.speaker_combo.clear()
        if speakers:
            self.speaker_combo.addItems(speakers)
            self.speaker_group.setVisible(True)
        else:
            self.speaker_group.setVisible(False)
            
        # Reset model when changing selection
        if self.synth is not None:
            self.synth = None
            self.status_label.setText("Model not loaded")
            self.speak_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            
        # Immediately load the model
        self.load_model()
        # Focus the text input after selecting model
        QTimer.singleShot(100, self.focus_text_entry)
        
    def on_cuda_change(self):
        """Handle CUDA setting change."""
        # Reset model when CUDA setting changes
        if self.synth is not None:
            self.synth = None
            self.status_label.setText("Model not loaded")
            self.speak_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
        # Immediately load the model
        self.load_model()
        
    def refresh_models(self):
        """Refresh the model list."""
        print("Refreshing models...")
        
        # Clear current models first
        self.model_combo.clear()
        self.desc_label.setText("Scanning for models...")
        
        # Scan for models
        models = get_available_models()
        model_names = [model["display_name"] for model in models]
        
        print(f"Refresh complete. Found {len(model_names)} models.")
        
        # Update combobox
        if model_names:
            for model in models:
                self.model_combo.addItem(model["display_name"], model)
            self.desc_label.setText(models[0].get("description", ""))
        else:
            self.model_combo.addItem("No models found")
            self.desc_label.setText("No models found")
        
        # Reset model
        if self.synth is not None:
            self.synth = None
            self.status_label.setText("Model not loaded")
            self.speak_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
        
        # Show results
        if model_names:
            QMessageBox.information(self, "Refresh Complete", f"Found {len(model_names)} model(s)")
        else:
            from tts_module.model_manager import get_models_directory
            models_dir = get_models_directory()
            QMessageBox.information(self, "Refresh Complete", f"No models found.\n\nPlease add models to:\n{models_dir}")
            
    def load_model(self):
        """Load the selected model."""
        if self._loading_model:
            return
            
        current_data = self.model_combo.currentData()
        if not current_data:
            return
            
        self._loading_model = True
        self.load_btn.setEnabled(False)
        self.status_label.setText("Loading model...")
        
        # Load model in background thread
        self.load_thread = ModelLoadThread(
            current_data["model_path"],
            current_data["config_path"],
            self.cuda_checkbox.isChecked()
        )
        self.load_thread.finished.connect(self.on_model_loaded)
        self.load_thread.error.connect(self.on_model_load_error)
        self.load_thread.start()
        
    def on_model_loaded(self, synth):
        """Handle successful model loading."""
        self.synth = synth
        self.status_label.setText("Model loaded successfully")
        self.speak_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self._loading_model = False
        
    def on_model_load_error(self, error_msg):
        """Handle model loading error."""
        self.status_label.setText("Model loading failed")
        self.load_btn.setEnabled(True)
        self._loading_model = False
        QMessageBox.critical(self, "Error", f"Failed to load model: {error_msg}")
        
    def queue_speak(self):
        """Add text to queue and trigger processing."""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter text to synthesize.")
            return
        if not self.synth:
            QMessageBox.warning(self, "Warning", "Please load a model first.")
            return
        with self.queue_lock:
            self.tts_queue.append(text)
        self.text_input.clear()
        QTimer.singleShot(0, self.update_queue_listbox)
        QTimer.singleShot(0, self.process_queue)

    def update_queue_listbox(self):
        """Update the queue listbox display, showing synthesizing status."""
        self.queue_listbox.clear()
        with self.queue_lock:
            for i, text in enumerate(self.tts_queue):
                if i == 0 and self._speaking:
                    display = f"{i+1}. {text[:50]}{'...' if len(text) > 50 else ''} (Synthesizing...)"
                else:
                    display = f"{i+1}. {text[:50]}{'...' if len(text) > 50 else ''}"
                self.queue_listbox.addItem(display)

    def process_queue(self):
        """Process the TTS queue: always speak from the queue, only one at a time."""
        if self._speaking:
            return
        with self.queue_lock:
            if not self.tts_queue:
                return
            text = self.tts_queue[0]  # Don't pop yet
        QTimer.singleShot(0, self.update_queue_listbox)
        speaker_id = None
        if self.speaker_group.isVisible() and self.speaker_combo.currentText():
            speaker_id = self.speaker_combo.currentText()
        self.synthesis_thread = SynthesisThread(
            self.model_combo.currentData()["model_path"],
            self.model_combo.currentData()["config_path"],
            text,
            speaker_id,
            self.cuda_checkbox.isChecked()
        )
        self.synthesis_thread.finished.connect(self.on_synthesis_finished)
        self.synthesis_thread.error.connect(self.on_synthesis_error)
        self.synthesis_thread.start()
        self._speaking = True
        QTimer.singleShot(0, lambda: self.speak_btn.setEnabled(False))
        QTimer.singleShot(0, self.update_queue_listbox)

    def on_synthesis_finished(self, wav):
        self.current_audio = wav
        self._speaking = False
        QTimer.singleShot(0, lambda: self.speak_btn.setEnabled(True))
        QTimer.singleShot(0, lambda: self.save_btn.setEnabled(True))
        # Remove the first item from the queue (just synthesized)
        with self.queue_lock:
            if self.tts_queue:
                self.tts_queue.popleft()
        QTimer.singleShot(0, self.update_queue_listbox)
        def play():
            try:
                play_audio(wav)
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Warning", f"Failed to play audio: {e}"))
            QTimer.singleShot(0, self.process_queue)
        threading.Thread(target=play, daemon=True).start()

    def on_synthesis_error(self, error_msg):
        self._speaking = False
        QTimer.singleShot(0, lambda: self.speak_btn.setEnabled(True))
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Synthesis failed: {error_msg}"))
        # Remove the first item from the queue (failed)
        with self.queue_lock:
            if self.tts_queue:
                self.tts_queue.popleft()
        QTimer.singleShot(0, self.update_queue_listbox)
        QTimer.singleShot(0, self.process_queue)
            
    def save_wav_file(self):
        """Save audio to WAV file."""
        if self.current_audio is None:
            QMessageBox.warning(self, "Warning", "No audio to save. Please synthesize first.")
            return
            
        # Get save path
        default_path = get_default_output_path()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Audio", default_path, "WAV Files (*.wav)"
        )
        
        if file_path:
            try:
                save_wav(self.current_audio, 22050, file_path)
                QMessageBox.information(self, "Success", f"Audio saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save audio: {e}")
                
    def remove_selected_from_queue(self):
        """Remove selected item from queue."""
        current_row = self.queue_listbox.currentRow()
        if current_row >= 0 and current_row < len(self.tts_queue):
            # Convert to list, remove item, convert back to deque
            queue_list = list(self.tts_queue)
            queue_list.pop(current_row)
            self.tts_queue = collections.deque(queue_list)
            self.update_queue_listbox()
            
    def clear_queue(self):
        """Clear the entire queue."""
        with self.queue_lock:
            self.tts_queue.clear()
        self.update_queue_listbox()
        
    def on_phonemizer_change(self, text):
        """Handle phonemizer selection change."""
        try:
            # Set environment variable
            os.environ["TTS_BACKEND"] = text
            print(f"Phonemizer set to: {text}")
            
            # Update config file if model is loaded
            current_data = self.model_combo.currentData()
            if current_data and current_data.get("config_path"):
                config_path = current_data["config_path"]
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        # Update the phonemizer in the config
                        config["phonemizer"] = text
                        
                        # Write the updated config back
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=4, ensure_ascii=False)
                        
                        print(f"✓ Updated config file {config_path} to use {text} phonemizer")
                        
                        # Reload the model to apply the new phonemizer
                        if self.synth is not None:
                            print("Reloading model to apply new phonemizer...")
                            self.load_model()
                            
                    except Exception as e:
                        print(f"Warning: Could not update config file: {e}")
                        
        except Exception as e:
            print(f"Error changing phonemizer: {e}")
        
    def set_hotkeys(self):
        """Open hotkey configuration dialog for a single hotkey."""
        dialog = HotkeyInputDialog(self.hotkey, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.hotkey = dialog.hotkey
            self.hotkey_btn.setText(f"Set Hotkey ({self.hotkey})")
            self.register_global_hotkey(self.hotkey)

    def import_custom_model(self):
        """Import custom model using original file dialog sequence."""
        from tts_module.model_manager import get_models_directory
        import shutil
        from PyQt6.QtWidgets import QInputDialog
        model_path, _ = QFileDialog.getOpenFileName(
            self, "Select Model File",
            "",
            "All Supported Models (*.pth *.pt *.ckpt *.safetensors);;PyTorch Model (*.pth);;PyTorch Checkpoint (*.pt);;Checkpoint (*.ckpt);;SafeTensors (*.safetensors)"
        )
        if not model_path:
            return
        config_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config .json File",
            "",
            "Config JSON (*.json)"
        )
        if not config_path:
            return
        # Check if config indicates multi-speaker
        is_multi_speaker = False
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            args = config_data.get("model_args", {})
            if args.get("use_speaker_embedding", False) or args.get("num_speakers", 1) > 1:
                is_multi_speaker = True
        except Exception as e:
            print(f"Warning: Could not parse config for multi-speaker check: {e}")
        # Optional: Speaker mapping file
        speaker_file_path, _ = QFileDialog.getOpenFileName(
            self, "(Optional) Select Speaker Mapping File (e.g., speakers.pth)",
            "",
            "Speaker Mapping (*.pth *.pt *.json *.pkl);;All Files (*)"
        )
        if is_multi_speaker and not speaker_file_path:
            QMessageBox.warning(
                self,
                "Speaker Mapping Recommended",
                "This model appears to be multi-speaker, but you did not select a speaker mapping file.\n\nYou can still import, but speaker names may not be available."
            )
        model_name, ok = QInputDialog.getText(self, "Model Name", "Enter a name for your custom model (no spaces):")
        if not ok or not model_name:
            return
        model_name = model_name.replace(" ", "_")
        models_dir = get_models_directory()
        dest_folder = os.path.join(models_dir, "custom", model_name)
        print(f"Importing custom model to: {dest_folder}")
        os.makedirs(dest_folder, exist_ok=True)
        dest_model = os.path.join(dest_folder, os.path.basename(model_path))
        dest_config = os.path.join(dest_folder, os.path.basename(config_path))
        shutil.copy2(model_path, dest_model)
        shutil.copy2(config_path, dest_config)
        if speaker_file_path:
            dest_speaker = os.path.join(dest_folder, "speakers.pth")
            shutil.copy2(speaker_file_path, dest_speaker)
            print(f"✓ Imported speaker mapping file as: {dest_speaker}")
        QMessageBox.information(self, "Success", f"Custom model imported as '{model_name}'.")
        self.refresh_models()

    def eventFilter(self, obj, event):
        if obj == self.text_input and isinstance(event, QKeyEvent):
            if event.type() == event.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    # Only add to queue and clear input, never block typing
                    self.queue_speak()
                    return True
        return super().eventFilter(obj, event)

    def register_global_hotkey(self, hotkey):
        """Register a global hotkey using the keyboard library, crash-free."""
        import keyboard
        # Remove previous hotkey handler if exists
        if hasattr(self, '_hotkey_handler') and self._hotkey_handler is not None:
            try:
                keyboard.remove_hotkey(self._hotkey_handler)
            except Exception:
                pass
            self._hotkey_handler = None
        # Validate hotkey before registering
        try:
            # Try to parse the hotkey first
            keyboard.parse_hotkey(hotkey)
        except Exception as e:
            err_msg = str(e)
            friendly = ""
            if "not mapped to any known key" in err_msg or "\\x" in err_msg:
                friendly = ("\n\nThis is usually because single-letter Ctrl+key combinations (like Ctrl+A) "
                            "are not supported as global hotkeys. Try using a combination with more modifiers, "
                            "such as Alt+T or Ctrl+/.\n")
            QMessageBox.warning(self, "Hotkey Error", f"Failed to register global hotkey '{hotkey}':\n{e}{friendly}\nThe error above is from the keyboard library.")
            return
        # Register new hotkey with suppress=True
        try:
            self._hotkey_handler = keyboard.add_hotkey(hotkey, lambda: QTimer.singleShot(0, self._toggle_window), suppress=True, trigger_on_release=False)
        except Exception as e:
            err_msg = str(e)
            friendly = ""
            if "not mapped to any known key" in err_msg or "\\x" in err_msg:
                friendly = ("\n\nThis is usually because single-letter Ctrl+key combinations (like Ctrl+A) "
                            "are not supported as global hotkeys. Try using a combination with more modifiers, "
                            "such as Alt+T or Ctrl+/.\n")
            QMessageBox.warning(self, "Hotkey Error", f"Failed to register global hotkey '{hotkey}':\n{e}{friendly}\nThe error above is from the keyboard library.")

    def _toggle_window(self):
        """Toggle window visibility with hotkey, robust and crash-free."""
        try:
            if self.isMinimized() or not self.isVisible():
                self.showNormal()
                self.raise_()
                self.activateWindow()
                self.is_minimized = False
                # Extra: On Windows, force window to front
                try:
                    import platform
                    if platform.system() == 'Windows':
                        import ctypes
                        hwnd = int(self.winId())
                        ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception:
                    pass
                self.focus_text_entry()
            else:
                self.showMinimized()
                self.is_minimized = True
        except Exception as e:
            print(f"Error toggling window: {e}")
            
    def _hotkey_speak(self):
        """Hotkey action for speaking text."""
        if self.synth and not self._speaking:
            text = self.text_input.toPlainText().strip()
            if text:
                self.queue_speak()
                
    def _hotkey_save(self):
        """Hotkey action for saving audio."""
        if self.current_audio is not None:
            self.save_wav_file()
            
    def _hotkey_focus(self):
        """Hotkey action for focusing text input."""
        self.focus_text_entry()
            
    def focus_text_entry(self):
        """Focus the text input field."""
        self.text_input.setFocus()
        
    def open_online_model_dialog(self):
        """Open online model download dialog."""
        dialog = OnlineModelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh models after successful download
            self.refresh_models()
        
    def _hotkey_speak(self):
        """Hotkey action for speaking text."""
        if self.synth and not self._speaking:
            text = self.text_input.toPlainText().strip()
            if text:
                self.queue_speak()
                
    def _hotkey_save(self):
        """Hotkey action for saving audio."""
        if self.current_audio is not None:
            self.save_wav_file()
            
    def _hotkey_focus(self):
        """Hotkey action for focusing text input."""
        self.focus_text_entry() 