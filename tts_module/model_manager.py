from TTS.utils.manage import ModelManager
import os
import sys
import json

def get_models_directory():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        models_dir = os.path.join(exe_dir, 'models')
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(script_dir, '..', 'models')
    return os.path.abspath(models_dir)

def find_config_file(folder_path, base_name):
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
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # (No-op: let users choose their own phonemizer)
        return False
    except Exception:
        return False

def get_model_type_from_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
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
    except Exception:
        return 'Unknown'

def get_model_size_mb(model_path):
    try:
        size = os.path.getsize(model_path)
        return size / (1024 * 1024)
    except Exception:
        return None

def is_tts_model_type(model_type):
    if not model_type:
        return False
    tts_types = ["vits", "tacotron", "fastpitch", "glow", "tacotron2", "capacitron"]
    vocoder_types = ["hifigan", "melgan", "vocoder"]
    model_type = model_type.lower()
    if any(v in model_type for v in vocoder_types):
        return False
    return any(t in model_type for t in tts_types)

def get_available_models():
    """Return a list of available TTS models with metadata."""
    models = []
    models_dir = get_models_directory()
    if not os.path.exists(models_dir):
        return models
    model_file_patterns = [
        '_model.pth', '_model.pt', '_model.ckpt', '_model.safetensors',
        '.pth', '.pt', '.ckpt', '.safetensors'
    ]
    non_model_filenames = [
        'speakers.pth', 'config.json', 'speakers.json', 'speakers.pkl',
        'language_ids.json', 'language_ids.pth', 'd_vector_file.pth', 'd_vector_file.json'
    ]
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if file.lower() in non_model_filenames:
                continue
            if not any(file.endswith(pattern) for pattern in model_file_patterns):
                continue
            folder_path = root
            model_name = file
            base_name = model_name.replace("_model.pth", "").replace("_model.pt", "").replace("_model.ckpt", "").replace("_model.safetensors", "").replace(".pth", "").replace(".pt", "").replace(".ckpt", "").replace(".safetensors", "")
            config_file = find_config_file(folder_path, base_name)
            if config_file:
                fix_phonemizer_config(config_file)
                model_type = get_model_type_from_config(config_file)
                if not is_tts_model_type(model_type):
                    continue
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
                size_mb = get_model_size_mb(os.path.join(root, file))
                size_str = f" [{size_mb:.1f} MB]" if size_mb else ""
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                args = config_data.get('model_args', {})
                use_speaker_embedding = args.get('use_speaker_embedding', False)
                num_speakers = args.get('num_speakers', 1)
                speakers_file = args.get('speakers_file', None)
                speakers_list = []
                if speakers_file:
                    speakers_path = os.path.join(os.path.dirname(config_file), speakers_file)
                    if os.path.exists(speakers_path):
                        try:
                            import torch
                            speakers_dict = torch.load(speakers_path, map_location='cpu')
                            if isinstance(speakers_dict, dict):
                                speakers_list = list(speakers_dict.keys())
                            elif isinstance(speakers_dict, list):
                                speakers_list = [str(i) for i in range(len(speakers_dict))]
                        except Exception:
                            pass
                if not speakers_list and (use_speaker_embedding or num_speakers > 1):
                    speakers_list = [str(i) for i in range(num_speakers)]
                model_speakers = speakers_list if (use_speaker_embedding or num_speakers > 1) else None
                models.append({
                    "display_name": display_name + size_str,
                    "model_path": os.path.join(root, file),
                    "config_path": config_file,
                    "model_type": model_type,
                    "folder": folder,
                    "description": f"{model_type} model in {folder_path} [{model_name}]{size_str}",
                    "speakers_list": model_speakers
                })
    return models 