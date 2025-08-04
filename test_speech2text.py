#!/usr/bin/env python3
"""
Test script to verify SPEECH2TEXT functionality with Xinference
"""

import sys
import os
import tempfile
import wave
import struct
import math

# Add the ragflow directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.db import LLMType
from api.db.services.llm_service import LLMBundle

def create_test_audio_file():
    """Create a simple test audio file (1 second of sine wave)"""
    duration = 1.0  # 1 second
    sample_rate = 16000
    frequency = 440.0  # A4 note
    
    # Generate sine wave
    samples = []
    for i in range(int(duration * sample_rate)):
        t = float(i) / sample_rate
        sample = int(32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Write samples
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    return temp_file.name

def test_speech2text():
    """Test SPEECH2TEXT model"""
    print("Testing SPEECH2TEXT model...")
    
    try:
        # Create test audio file
        print("Creating test audio file...")
        audio_file = create_test_audio_file()
        
        try:
            # Read audio file as binary
            with open(audio_file, 'rb') as f:
                audio_binary = f.read()
            
            print(f"Created test audio file: {len(audio_binary)} bytes")
            
            # Initialize LLMBundle for SPEECH2TEXT
            print("Initializing SPEECH2TEXT LLMBundle...")
            tenant_id = "69736c5e723611efab910242ac120004"  # Use the tenant ID from our previous queries
            
            seq2txt_bundle = LLMBundle(tenant_id, LLMType.SPEECH2TEXT, lang="English")
            
            print(f"Model: {seq2txt_bundle.llm_name}")
            print(f"Model type: {seq2txt_bundle.llm_type}")
            
            # Test transcription
            print("Testing transcription...")
            result = seq2txt_bundle.transcription(audio_binary)
            
            print(f"Transcription result: {result}")
            print("✅ SPEECH2TEXT test successful!")
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
                
    except Exception as e:
        print(f"❌ SPEECH2TEXT test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_speech2text()
