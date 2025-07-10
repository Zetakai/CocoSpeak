from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QProgressBar, QLineEdit,
                             QFileDialog, QMessageBox, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import os
import json
import shutil
from TTS.utils.manage import ModelManager

class OnlineModelDialog(QDialog):
    """Dialog for downloading online models."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download TTS Model")
        self.setFixedSize(700, 500)
        self.setModal(True)
        
        # Initialize variables
        self.model_ids = []
        self.model_names = []
        
        self.setup_ui()
        self.fetch_models()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Select Model to Download")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Choose a model from the Coqui TTS Hub to download:")
        desc_label.setFont(QFont("Arial", 10))
        layout.addWidget(desc_label)
        
        # Model list
        self.model_list = QListWidget()
        layout.addWidget(self.model_list)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download Selected Model")
        self.download_btn.clicked.connect(self.download_selected)
        self.download_btn.setEnabled(False)
        button_layout.addWidget(self.download_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def fetch_models(self):
        """Fetch available models from TTS Hub."""
        self.status_label.setText("Fetching model list...")
        self.fetch_thread = ModelFetchThread()
        self.fetch_thread.finished.connect(self.on_models_fetched)
        self.fetch_thread.error.connect(self.on_fetch_error)
        self.fetch_thread.start()
        
    def on_models_fetched(self, model_ids, model_names):
        """Handle successful model fetch."""
        self.model_ids = model_ids
        self.model_names = model_names
        
        # Populate list
        self.model_list.clear()
        for name in model_names:
            self.model_list.addItem(name)
            
        self.status_label.setText(f"Found {len(model_names)} TTS models")
        self.download_btn.setEnabled(True)
        
    def on_fetch_error(self, error_msg):
        """Handle fetch error."""
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to fetch model list: {error_msg}")
        
    def download_selected(self):
        """Download the selected model."""
        current_row = self.model_list.currentRow()
        if current_row < 0:
            self.status_label.setText("Please select a model to download.")
            return
            
        model_id = self.model_ids[current_row]
        model_name = self.model_names[current_row]
        
        # Start download
        self.download_thread = ModelDownloadThread(model_id, model_name)
        self.download_thread.progress.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()
        
        self.download_btn.setEnabled(False)
        self.status_label.setText("Downloading model...")
        
    def update_download_progress(self, progress, message):
        """Update download progress."""
        self.status_label.setText(f"Downloading: {message} ({progress}%)")
        
    def on_download_finished(self, message):
        """Handle successful download."""
        self.status_label.setText("Download completed!")
        QMessageBox.information(self, "Success", f"Model downloaded successfully!\n{message}")
        self.accept()
        
    def on_download_error(self, error_msg):
        """Handle download error."""
        self.status_label.setText(f"Download failed: {error_msg}")
        self.download_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Download failed: {error_msg}")

class ModelFetchThread(QThread):
    """Thread for fetching model list."""
    finished = pyqtSignal(list, list)  # model_ids, model_names
    error = pyqtSignal(str)
    
    def run(self):
        try:
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
            
            if not filtered_model_ids:
                self.error.emit("No TTS models found in the online model list.")
                return
                
            self.finished.emit(filtered_model_ids, model_names)
            
        except Exception as e:
            self.error.emit(str(e))

class ModelDownloadThread(QThread):
    """Thread for downloading models."""
    progress = pyqtSignal(int, str)  # progress_percent, message
    finished = pyqtSignal(str)  # success message
    error = pyqtSignal(str)
    
    def __init__(self, model_id, model_name):
        super().__init__()
        self.model_id = model_id
        self.model_name = model_name
        
    def run(self):
        try:
            manager = ModelManager()
            
            # Download the model
            self.progress.emit(0, "Starting download...")
            manager.download_model(self.model_id)
            self.progress.emit(100, "Download completed")
            
            self.finished.emit(f"Model '{self.model_name}' has been downloaded successfully.")
            
        except Exception as e:
            self.error.emit(str(e))

class CustomModelImportDialog(QDialog):
    """Dialog for importing custom models."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Custom Model")
        self.setFixedSize(500, 300)
        self.setModal(True)
        
        self.model_path = ""
        self.config_path = ""
        self.speaker_path = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Import Custom Model")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Model file selection
        model_group = QGroupBox("Model File")
        model_layout = QVBoxLayout()
        
        self.model_label = QLabel("No model file selected")
        model_layout.addWidget(self.model_label)
        
        model_btn = QPushButton("Select Model File")
        model_btn.clicked.connect(self.select_model_file)
        model_layout.addWidget(model_btn)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Config file selection
        config_group = QGroupBox("Config File")
        config_layout = QVBoxLayout()
        
        self.config_label = QLabel("No config file selected")
        config_layout.addWidget(self.config_label)
        
        config_btn = QPushButton("Select Config File")
        config_btn.clicked.connect(self.select_config_file)
        config_layout.addWidget(config_btn)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Speaker file selection (optional)
        speaker_group = QGroupBox("Speaker Mapping File (Optional)")
        speaker_layout = QVBoxLayout()
        
        self.speaker_label = QLabel("No speaker file selected")
        speaker_layout.addWidget(self.speaker_label)
        
        speaker_btn = QPushButton("Select Speaker File")
        speaker_btn.clicked.connect(self.select_speaker_file)
        speaker_layout.addWidget(speaker_btn)
        
        speaker_group.setLayout(speaker_layout)
        layout.addWidget(speaker_group)
        
        # Model name input
        name_group = QGroupBox("Model Name")
        name_layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter model name (no spaces)")
        name_layout.addWidget(self.name_input)
        
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import Model")
        self.import_btn.clicked.connect(self.import_model)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def select_model_file(self):
        """Select model file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Model File",
            "",
            "All Supported Models (*.pth *.pt *.ckpt *.safetensors);;PyTorch Model (*.pth);;PyTorch Checkpoint (*.pt);;Checkpoint (*.ckpt);;SafeTensors (*.safetensors)"
        )
        if file_path:
            self.model_path = file_path
            self.model_label.setText(os.path.basename(file_path))
            self.check_import_ready()
            
    def select_config_file(self):
        """Select config file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File",
            "",
            "Config JSON (*.json)"
        )
        if file_path:
            self.config_path = file_path
            self.config_label.setText(os.path.basename(file_path))
            self.check_import_ready()
            
    def select_speaker_file(self):
        """Select speaker mapping file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Speaker Mapping File",
            "",
            "Speaker Mapping (*.pth *.pt *.json *.pkl);;All Files (*)"
        )
        if file_path:
            self.speaker_path = file_path
            self.speaker_label.setText(os.path.basename(file_path))
            
    def check_import_ready(self):
        """Check if import is ready."""
        ready = bool(self.model_path and self.config_path and self.name_input.text().strip())
        self.import_btn.setEnabled(ready)
        
    def import_model(self):
        """Import the custom model."""
        try:
            model_name = self.name_input.text().strip().replace(" ", "_")
            if not model_name:
                QMessageBox.warning(self, "Error", "Please enter a model name.")
                return
                
            # Check if config indicates multi-speaker
            is_multi_speaker = False
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                args = config_data.get("model_args", {})
                if args.get("use_speaker_embedding", False) or args.get("num_speakers", 1) > 1:
                    is_multi_speaker = True
            except Exception as e:
                print(f"Warning: Could not parse config for multi-speaker check: {e}")
                
            if is_multi_speaker and not self.speaker_path:
                reply = QMessageBox.question(
                    self, "Speaker Mapping Recommended",
                    "This model appears to be multi-speaker, but you did not select a speaker mapping file.\n\nYou can still import, but speaker names may not be available.\n\nContinue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                    
            # Import the model
            from tts_module.model_manager import get_models_directory
            models_dir = get_models_directory()
            dest_folder = os.path.join(models_dir, "custom", model_name)
            
            print(f"Importing custom model to: {dest_folder}")
            os.makedirs(dest_folder, exist_ok=True)
            
            dest_model = os.path.join(dest_folder, os.path.basename(self.model_path))
            dest_config = os.path.join(dest_folder, os.path.basename(self.config_path))
            
            shutil.copy2(self.model_path, dest_model)
            shutil.copy2(self.config_path, dest_config)
            
            # Copy speaker mapping file if provided
            if self.speaker_path:
                dest_speaker = os.path.join(dest_folder, "speakers.pth")
                shutil.copy2(self.speaker_path, dest_speaker)
                print(f"✓ Imported speaker mapping file as: {dest_speaker}")
                
            QMessageBox.information(self, "Success", f"Custom model imported as '{model_name}'.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import custom model: {e}")

class HotkeyDialog(QDialog):
    """Dialog for setting hotkeys."""
    
    def __init__(self, current_hotkeys, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Hotkeys")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.current_hotkeys = current_hotkeys.copy()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Configure Hotkeys")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Hotkey list
        self.hotkey_list = QListWidget()
        self.populate_hotkey_list()
        layout.addWidget(self.hotkey_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Hotkey")
        add_btn.clicked.connect(self.add_hotkey)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit Hotkey")
        edit_btn.clicked.connect(self.edit_hotkey)
        button_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove Hotkey")
        remove_btn.clicked.connect(self.remove_hotkey)
        button_layout.addWidget(remove_btn)
        
        layout.addLayout(button_layout)
        
        # OK/Cancel buttons
        ok_cancel_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_cancel_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_cancel_layout.addWidget(cancel_btn)
        
        layout.addLayout(ok_cancel_layout)
        self.setLayout(layout)
        
    def populate_hotkey_list(self):
        """Populate the hotkey list."""
        self.hotkey_list.clear()
        for action, hotkey in self.current_hotkeys.items():
            self.hotkey_list.addItem(f"{action}: {hotkey}")
            
    def add_hotkey(self):
        """Add a new hotkey."""
        # TODO: Implement hotkey input dialog
        QMessageBox.information(self, "Add Hotkey", "Hotkey addition not yet implemented")
        
    def edit_hotkey(self):
        """Edit selected hotkey."""
        current_row = self.hotkey_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a hotkey to edit.")
            return
            
        # TODO: Implement hotkey editing
        QMessageBox.information(self, "Edit Hotkey", "Hotkey editing not yet implemented")
        
    def remove_hotkey(self):
        """Remove selected hotkey."""
        current_row = self.hotkey_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a hotkey to remove.")
            return
            
        # TODO: Implement hotkey removal
        QMessageBox.information(self, "Remove Hotkey", "Hotkey removal not yet implemented") 