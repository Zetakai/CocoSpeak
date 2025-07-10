import sounddevice as sd
import soundfile as sf
import numpy as np
import os

def play_audio(wav, sample_rate=22050):
    """Play audio using sounddevice."""
    try:
        # Ensure audio is in the correct format
        if wav.dtype != np.float32:
            wav = wav.astype(np.float32)
        
        # Normalize audio to prevent clipping
        max_val = np.max(np.abs(wav))
        if max_val > 0:
            wav = wav / max_val * 0.8
        
        # Play the audio
        sd.play(wav, sample_rate)
        sd.wait()  # Wait for playback to finish
        
        print("Audio playback completed")
        
    except Exception as e:
        print(f"Audio playback failed: {e}")
        raise Exception(f"Audio playback failed: {e}")

def save_wav(wav, sample_rate, file_path):
    """Save audio to WAV file."""
    try:
        # Ensure audio is in the correct format
        if wav.dtype != np.float32:
            wav = wav.astype(np.float32)
        
        # Normalize audio to prevent clipping
        max_val = np.max(np.abs(wav))
        if max_val > 0:
            wav = wav / max_val * 0.95
        
        # Save the audio
        sf.write(file_path, wav, sample_rate)
        
        print(f"Audio saved to: {file_path}")
        
    except Exception as e:
        print(f"Failed to save audio: {e}")
        raise Exception(f"Failed to save audio: {e}")

def get_default_output_path():
    """Get default output path for saved audio files."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"cocospeak_output_{timestamp}.wav" 