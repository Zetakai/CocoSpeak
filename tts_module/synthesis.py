from TTS.utils.synthesizer import Synthesizer
import os
import sys
import numpy as np
import torch

def load_model(model_path, config_path, use_cuda=False):
    """Load a TTS model from the given paths."""
    try:
        # Temporarily change working directory to model folder for speakers.pth
        original_cwd = os.getcwd()
        model_dir = os.path.dirname(config_path)
        os.chdir(model_dir)
        
        # Load the synthesizer
        synth = Synthesizer(
            model_path,
            config_path,
            None,  # vocoder_path
            None,  # vocoder_config_path
            None,  # encoder_path
            None,  # encoder_config_path
            use_cuda=use_cuda
        )
        
        # Restore original working directory
        os.chdir(original_cwd)
        
        return synth
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None

def tts_to_wav(synth, text, speaker_id=None):
    """Convert text to speech using the loaded synthesizer. Tries all speaker argument names for multi-speaker models."""
    if synth is None:
        raise Exception("Model not loaded. Please load the model first.")
    
    try:
        print(f"Starting TTS synthesis for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"Text length: {len(text)} characters")
        
        wav = None
        errors = []
        if speaker_id is not None:
            # Try all common argument names for multi-speaker models
            try:
                wav = synth.tts(text, speaker=speaker_id)
            except Exception as e1:
                errors.append(f"speaker: {e1}")
                try:
                    wav = synth.tts(text, speaker_idx=speaker_id)
                except Exception as e2:
                    errors.append(f"speaker_idx: {e2}")
                    try:
                        wav = synth.tts(text, speaker_id=speaker_id)
                    except Exception as e3:
                        errors.append(f"speaker_id: {e3}")
                        try:
                            wav = synth.tts(text, speaker_name=str(speaker_id))
                        except Exception as e4:
                            errors.append(f"speaker_name: {e4}")
                            try:
                                wav = synth.tts(text, speaker_id)
                            except Exception as e5:
                                errors.append(f"positional: {e5}")
            if wav is None:
                raise Exception("All attempts to synthesize with speaker failed: " + " | ".join(errors))
        else:
            wav = synth.tts(text)
        print("TTS synthesis completed successfully")
        
        # Convert to numpy array
        if isinstance(wav, list):
            if all(isinstance(x, (float, int, np.floating, np.integer)) for x in wav):
                wav = np.array(wav, dtype=np.float32)
            elif all(hasattr(x, '__len__') for x in wav):
                wav = np.concatenate([np.asarray(seg, dtype=np.float32) for seg in wav if seg is not None and len(seg) > 0])
            else:
                wav = np.array(wav, dtype=np.float32)
        elif not isinstance(wav, np.ndarray):
            wav = np.array(wav, dtype=np.float32)
        
        # Add silence buffer
        buffer_samples = int(22050 * 0.5)  # 0.5 seconds of silence
        silence_buffer = np.zeros(buffer_samples, dtype=wav.dtype)
        wav = np.concatenate([wav, silence_buffer])
        
        # Improve audio clarity
        wav = improve_audio_clarity(wav)
        
        return wav
        
    except Exception as e:
        print(f"TTS synthesis failed: {e}")
        raise Exception(f"TTS synthesis failed: {e}")

def improve_audio_clarity(wav):
    """Improve audio clarity with enhanced processing."""
    try:
        # Ensure audio is float32
        wav = wav.astype(np.float32)
        
        # Normalize audio
        max_val = np.max(np.abs(wav))
        if max_val > 0:
            wav = wav / max_val * 0.95
        
        # Apply gentle compression
        threshold = 0.7
        ratio = 4.0
        wav_compressed = np.where(
            np.abs(wav) > threshold,
            threshold + (np.abs(wav) - threshold) / ratio * np.sign(wav),
            wav
        )
        
        return wav_compressed
        
    except Exception as e:
        print(f"Audio processing failed: {e}")
        return wav

def debug_audio_info(wav, stage=""):
    """Debug function to print audio information."""
    try:
        print(f"DEBUG {stage}:")
        print(f"  Shape: {wav.shape}")
        print(f"  Data type: {wav.dtype}")
        print(f"  Min value: {np.min(wav)}")
        print(f"  Max value: {np.max(wav)}")
        print(f"  Mean value: {np.mean(wav)}")
        print(f"  Has NaN: {np.isnan(wav).any()}")
        print(f"  Has Inf: {np.isinf(wav).any()}")
        print(f"  Non-zero samples: {np.count_nonzero(wav)}")
        print(f"  Total samples: {len(wav)}")
    except Exception as e:
        print(f"DEBUG {stage}: Error getting audio info: {e}") 