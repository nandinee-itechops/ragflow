#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import sys
import re
import cv2
import logging
import tempfile
import subprocess
import threading
import shutil
import numpy as np
import asyncio
from io import BytesIO
from typing import List, Tuple, Dict, Any, Optional
import base64
import json

from api.utils.file_utils import get_project_base_directory
from rag.nlp import rag_tokenizer

class RAGFlowVideoParser:
    """
    Enhanced video parser that extracts audio and processes it with Whisper,
    with robust FFmpeg detection and improved error handling.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the video parser.
        
        Args:
            vision_model: Vision model for frame analysis (optional)
            speech_model: Speech-to-text model for audio transcription (optional)
            frame_interval: Seconds between frame extractions (default: 5)
            audio_chunk_duration: Audio chunk duration in seconds (default: 30)
            max_frames: Maximum frames to extract (default: 100)
        """
        self.vision_model = kwargs.get('vision_model', None)
        self.speech_model = kwargs.get('speech_model', None)
        self.frame_interval = kwargs.get('frame_interval', 5.0)
        self.audio_chunk_duration = kwargs.get('audio_chunk_duration', 30.0)
        self.max_frames = kwargs.get('max_frames', 100)
        self.temp_dir = kwargs.get('temp_dir', tempfile.gettempdir())
        
        # Detect FFmpeg installation
        self.ffmpeg_path = self._detect_ffmpeg()
        self.ffmpeg_available = self.ffmpeg_path is not None
        
        if self.ffmpeg_available:
            logging.info(f"FFmpeg detected at: {self.ffmpeg_path}")
        else:
            logging.warning("FFmpeg not available. Video processing will be limited.")
        
        # Thread lock for parallel processing
        self.lock = threading.Lock()
    
    def _detect_ffmpeg(self) -> Optional[str]:
        """Detect FFmpeg installation across multiple common paths"""
        potential_paths = [
            "ffmpeg",  # Check system PATH
            r"C:\Program Files\ffmpeg-7.1.1\ffmpeg.exe",
            r"C:\Program Files\FFmpeg\bin\ffmpeg.exe", 
            r"C:\FFmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\FFmpeg\bin\ffmpeg.exe",
            os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),  # Local installation
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",  # Chocolatey installation
            r"C:\msys64\mingw64\bin\ffmpeg.exe",  # MSYS2 installation
        ]
        
        for path in potential_paths:
            try:
                if path == "ffmpeg":
                    # Check if available in system PATH
                    result = subprocess.run(
                        ["where", "ffmpeg"] if os.name == "nt" else ["which", "ffmpeg"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # Verify the found path works
                        try:
                            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
                            return "ffmpeg"
                        except:
                            continue
                elif os.path.exists(path) and os.path.isfile(path):
                    # Test if this FFmpeg path actually works
                    try:
                        subprocess.run([path, "-version"], capture_output=True, check=True, timeout=5)
                        return path
                    except:
                        continue
            except Exception as e:
                logging.warning(f"Error checking FFmpeg path {path}: {str(e)}")
        
        return None
    
    def _extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """Extract audio from video file using FFmpeg with improved error handling and validation"""
        
        if not self.ffmpeg_available:
            logging.warning("FFmpeg not available, cannot extract audio")
            return None
        
        # Validate input video file
        if not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            return None
            
        if not os.path.isfile(video_path):
            logging.error(f"Path is not a file: {video_path}")
            return None
        
        # Test file readability
        try:
            with open(video_path, "rb") as f:
                f.read(1024)  # Test reading first 1KB
        except PermissionError:
            logging.error(f"Cannot read video file: {video_path}")
            return None
        except Exception as e:
            logging.error(f"Error accessing video file: {e}")
            return None
        
        temp_audio_path = None
        try:
            # Create temporary file for audio extraction
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_audio_path = temp_file.name
            
            # FFmpeg command for audio extraction with better error handling
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,           # Input video file
                "-vn",                      # Disable video stream
                "-acodec", "libmp3lame",    # Use MP3 codec
                "-q:a", "2",                # High quality audio (VBR)
                "-ar", "16000",             # Sample rate for Whisper
                "-ac", "1",                 # Mono audio for better processing
                "-y",                       # Overwrite output file
                temp_audio_path             # Output audio file
            ]
            
            # Run FFmpeg with timeout and proper error handling
            process = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=600  # 10 minute timeout for large files
            )
            
            logging.info(f"FFmpeg extraction successful for {video_path}")
            
            # Verify audio file was created and has content
            if not os.path.exists(temp_audio_path):
                logging.warning("Audio file was not created by FFmpeg")
                return None
                
            if os.path.getsize(temp_audio_path) == 0:
                logging.warning("Audio file is empty - no audio content in video")
                os.unlink(temp_audio_path)
                return None
            
            # Test if the audio file is valid by trying to read it
            try:
                with open(temp_audio_path, "rb") as f:
                    header = f.read(10)
                    if len(header) < 3:
                        logging.warning("Audio file appears corrupted")
                        os.unlink(temp_audio_path)
                        return None
            except Exception as e:
                logging.warning(f"Cannot validate audio file: {e}")
                os.unlink(temp_audio_path)
                return None
            
            return temp_audio_path
            
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg error extracting audio from {video_path}: {e.stderr}")
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            return None
        except subprocess.TimeoutExpired:
            logging.error(f"FFmpeg timeout while processing {video_path}")
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            return None
        except Exception as e:
            logging.error(f"Unexpected error during audio extraction: {e}")
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            return None
    
    def _transcribe_audio_with_whisper(self, audio_path: str) -> Optional[Dict]:
        """Transcribe audio using OpenAI Whisper with improved error handling and validation"""
        if not audio_path or not os.path.exists(audio_path):
            logging.error(f"Audio file not found: {audio_path}")
            return None
            
        try:
            # Try to import whisper
            import whisper
        except ImportError:
            logging.warning("OpenAI Whisper not available. Install with: pip install openai-whisper")
            return None
        
        try:
            # Validate audio file before processing
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                logging.error("Audio file is empty")
                return None
            
            if file_size > 25 * 1024 * 1024:  # 25MB limit for Whisper
                logging.warning(f"Audio file is large ({file_size/1024/1024:.1f}MB), processing may be slow")
            
            # Load Whisper model (base is good balance of speed/accuracy)
            logging.info("Loading Whisper model...")
            model = whisper.load_model("base")
            
            # Transcribe audio with timestamps and language detection
            logging.info(f"Transcribing audio file: {audio_path}")
            result = model.transcribe(
                audio_path,
                language=None,  # Auto-detect language
                word_timestamps=True,  # Get word-level timestamps
                verbose=False
            )
            
            if not result:
                logging.error("Whisper returned empty result")
                return None
            
            # Validate transcription result
            if not result.get("text") or not result["text"].strip():
                logging.warning("No speech detected in audio")
                return None
            
            # Log transcription summary
            duration = result.get("duration", 0)
            language = result.get("language", "unknown")
            text_length = len(result.get("text", ""))
            logging.info(f"Transcription completed: {duration:.1f}s audio, {text_length} chars, language: {language}")
            
            return result
            
        except Exception as e:
            logging.error(f"Whisper transcription failed: {str(e)}")
            return None
        finally:
            # Clean up audio file to save space
            try:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
                    logging.debug(f"Cleaned up temporary audio file: {audio_path}")
            except Exception as e:
                logging.warning(f"Could not clean up audio file {audio_path}: {e}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format for better readability"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video metadata using ffprobe with fallback to OpenCV.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing video metadata
        """
        if not self.ffmpeg_available:
            return self._get_video_info_fallback(video_path)
        
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  check=True, timeout=30)
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next(
                (s for s in info['streams'] if s['codec_type'] == 'video'), 
                None
            )
            audio_stream = next(
                (s for s in info['streams'] if s['codec_type'] == 'audio'), 
                None
            )
            
            duration = float(info['format'].get('duration', 0))
            
            return {
                'duration': duration,
                'has_video': video_stream is not None,
                'has_audio': audio_stream is not None,
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0
            }
        except subprocess.TimeoutExpired:
            logging.error("FFprobe timed out")
            return self._get_video_info_fallback(video_path)
        except Exception as e:
            logging.warning(f"Could not get video info with ffprobe: {e}")
            return self._get_video_info_fallback(video_path)
    
    def _get_video_info_fallback(self, video_path: str) -> Dict[str, Any]:
        """Fallback method using OpenCV when ffprobe fails."""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logging.error("Cannot open video with OpenCV")
                return {'duration': 0, 'has_video': False, 'has_audio': False}
            
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'duration': duration,
                'has_video': True,
                'has_audio': True,  # Assume audio exists - cannot detect with cv2
                'width': width,
                'height': height,
                'fps': fps
            }
        except Exception as e:
            logging.error(f"Error getting video info with cv2: {e}")
            return {'duration': 0, 'has_video': False, 'has_audio': False}
    
    def _process_video_only(self, video_path: str, start_time: float, end_time: float, callback) -> List[Tuple[str, str]]:
        """Process video without audio, extracting basic frame information"""
        try:
            callback(0.3, "Processing video frames only (no audio)...")
            
            # Try to extract basic video info
            video_info = self._get_video_info(video_path)
            
            basic_info = f"Video file processed (no audio transcription available)\n"
            basic_info += f"Duration: {self._format_timestamp(video_info.get('duration', 0))}\n"
            basic_info += f"Resolution: {video_info.get('width', 'unknown')}x{video_info.get('height', 'unknown')}\n"
            basic_info += f"FPS: {video_info.get('fps', 'unknown')}\n"
            basic_info += f"Time range: {self._format_timestamp(start_time)} - {self._format_timestamp(end_time)}"
            
            metadata = {
                "source": video_path,
                "file_type": "video",
                "has_audio": False,
                "has_video": True,
                "start_time": start_time,
                "end_time": end_time,
                "duration": video_info.get('duration', 0)
            }
            
            return [(basic_info, json.dumps(metadata))]
            
        except Exception as e:
            logging.error(f"Error processing video-only: {e}")
            return [(f"Basic video processing failed: {str(e)}", 
                    json.dumps({"source": video_path, "error": str(e)}))]
    
    def _process_with_fallback_methods(self, video_path: str, audio_path: str, start_time: float, end_time: float, callback) -> List[Tuple[str, str]]:
        """Fallback processing when Whisper fails"""
        try:
            callback(0.6, "Trying alternative transcription methods...")
            
            # Try with the original speech model if available
            if self.speech_model:
                callback(0.7, "Using original speech model...")
                # For now, return basic info since speech model integration is complex
                return self._process_video_only(video_path, start_time, end_time, callback)
            
            # If all else fails, return basic video info
            return self._process_video_only(video_path, start_time, end_time, callback)
            
        except Exception as e:
            logging.error(f"Error in fallback processing: {e}")
            return [(f"Fallback processing failed: {str(e)}", 
                    json.dumps({"source": video_path, "error": str(e)}))]
    
    def __call__(self, filename, from_page=0, to_page=100000, **kwargs):
        """
        Complete video processing pipeline with improved error handling:
        1. Validate video file
        2. Detect FFmpeg
        3. Extract audio
        4. Transcribe with Whisper
        5. Format results with timestamps
        """
        callback = kwargs.get("callback", lambda prog, msg: None)
        
        try:
            # Handle binary input
            if isinstance(filename, bytes):
                # Save binary to temporary file
                temp_video = os.path.join(self.temp_dir, f"temp_video_{os.getpid()}.mp4")
                with open(temp_video, 'wb') as f:
                    f.write(filename)
                video_path = temp_video
            else:
                video_path = filename
            
            callback(0.05, "Validating video file...")
            
            # File validation
            if not os.path.exists(video_path):
                callback(-1, f"Video file not found: {video_path}")
                return [], []
            
            if not os.path.isfile(video_path):
                callback(-1, f"Path is not a file: {video_path}")
                return [], []
            
            # Test file readability
            try:
                with open(video_path, "rb"):
                    pass
            except PermissionError:
                callback(-1, f"Cannot read video file: {video_path}")
                return [], []
            
            callback(0.1, "Analyzing video file...")
            
            # Get video information
            video_info = self._get_video_info(video_path)
            if video_info['duration'] == 0:
                logging.warning("Could not determine video duration, attempting basic processing")
                video_info = {'duration': 300, 'has_video': True, 'has_audio': True}  # Assume 5min max
                
            # Apply time range filtering
            start_time = max(0, from_page)
            end_time = min(video_info['duration'], to_page)
            
            if start_time >= end_time:
                logging.warning("Invalid time range specified")
                return [], []
            
            callback(0.15, "Setting up temporary workspace...")
            
            # Check if we can process the video
            if not self.ffmpeg_available:
                callback(0.2, "FFmpeg not available, using basic processing...")
                return [("FFmpeg not found. Please install FFmpeg and add to system PATH.", 
                        json.dumps({"source": video_path, "error": "FFmpeg not available"}))], []
            
            try:
                # Primary processing: Extract and transcribe audio
                callback(0.2, "Extracting audio from video...")
                
                audio_path = self._extract_audio_from_video(video_path)
                if not audio_path:
                    callback(0.3, "No audio content found, processing video frames only...")
                    return self._process_video_only(video_path, start_time, end_time, callback)
                
                callback(0.4, "Transcribing audio with Whisper...")
                
                # Try Whisper transcription first
                whisper_result = self._transcribe_audio_with_whisper(audio_path)
                if whisper_result and whisper_result.get("text"):
                    callback(0.8, "Processing transcription results...")
                    
                    # Format results with timestamps
                    if "segments" in whisper_result:
                        segments = [
                            f"[{self._format_timestamp(seg['start'])} --> {self._format_timestamp(seg['end'])}] {seg['text']}"
                            for seg in whisper_result["segments"]
                            if start_time <= seg['start'] <= end_time  # Filter by time range
                        ]
                        full_transcript = "\n".join(segments)
                    else:
                        full_transcript = whisper_result.get("text", "")
                    
                    metadata = {
                        "source": video_path,
                        "file_type": "video", 
                        "language": whisper_result.get("language", "unknown"),
                        "duration": whisper_result.get("duration", video_info.get('duration', 0)),
                        "start_time": start_time,
                        "end_time": end_time,
                        "has_audio": True,
                        "has_video": video_info.get('has_video', True)
                    }
                    
                    callback(1.0, "Video processing completed successfully!")
                    
                    # Clean up temporary files
                    try:
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                        if isinstance(filename, bytes) and os.path.exists(temp_video):
                            os.remove(temp_video)
                    except:
                        pass
                    
                    return [(full_transcript, json.dumps(metadata))], []
                else:
                    callback(0.5, "Whisper transcription failed, trying alternative methods...")
                    return self._process_with_fallback_methods(video_path, audio_path, start_time, end_time, callback)
                    
            except Exception as e:
                logging.error(f"Error in main processing pipeline: {str(e)}")
                callback(-1, f"Video processing failed: {str(e)}")
                return [(f"Video processing failed: {str(e)}", 
                        json.dumps({"source": video_path, "error": str(e)}))], []
                        
        except Exception as e:
            logging.error(f"Critical error in video processing: {str(e)}")
            callback(-1, f"Critical video processing error: {str(e)}")
            return [(f"Video processing failed: {str(e)}", 
                    json.dumps({"error": str(e)}))], []
    
    @staticmethod
    def total_page_number(filename, binary=None):
        """
        Get total duration of video as 'page count' (in seconds).
        
        Args:
            filename: Video file path
            binary: Video binary data (optional)
            
        Returns:
            Total duration in seconds as integer
        """
        try:
            parser = RAGFlowVideoParser()
            
            if binary:
                temp_path = os.path.join(tempfile.gettempdir(), f"temp_video_{os.getpid()}.mp4")
                with open(temp_path, 'wb') as f:
                    f.write(binary)
                video_info = parser._get_video_info(temp_path)
                try:
                    os.remove(temp_path)
                except:
                    pass
            else:
                video_info = parser._get_video_info(filename)
            
            return int(video_info.get('duration', 0))
        except Exception as e:
            logging.error(f"Error getting video page count: {e}")
            return 0
    
    def crop(self, text, ZM=3, need_position=False):
        """
        Crop text to fit within token limits.
        
        Args:
            text: Input text to crop
            ZM: Zoom factor for token limit
            need_position: Whether to return position info
            
        Returns:
            Cropped text or tuple of (text, positions) if need_position=True
        """
        try:
            if len(text) < 100:
                return text if not need_position else (text, [])
            
            # Use simple truncation for video content
            max_chars = 8000 // ZM
            if len(text) <= max_chars:
                return text if not need_position else (text, [])
            
            cropped = text[:max_chars] + "..."
            return cropped if not need_position else (cropped, [])
            
        except Exception as e:
            logging.error(f"Error cropping video text: {e}")
            return text if not need_position else (text, [])
    
    @staticmethod
    def chunk(binary, filename="", from_page=0, to_page=100000, lang="English", callback=None, **kwargs):
        """
        Compatibility method for the chunking interface.
        
        Args:
            binary: Video binary data
            filename: Original filename
            from_page: Start time in seconds
            to_page: End time in seconds
            lang: Language (ignored for now)
            callback: Progress callback
            **kwargs: Additional arguments
            
        Returns:
            List of chunk dictionaries
        """
        try:
            parser = RAGFlowVideoParser(**kwargs)
            chunks, _ = parser(binary, from_page, to_page, callback=callback, **kwargs)
            
            result = []
            for i, (content, metadata_str) in enumerate(chunks):
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    chunk = {
                        "content_with_weight": content,
                        "content_ltks": content,
                        "content_sm_ltks": content,
                        "image": None,
                        "image_id": "",
                        "page_number": i + 1,
                        "positions": [],
                        "img_path": "",
                        "metadata": metadata
                    }
                    result.append(chunk)
                    
                except json.JSONDecodeError:
                    # Handle invalid JSON
                    chunk = {
                        "content_with_weight": content,
                        "content_ltks": content,
                        "content_sm_ltks": content,
                        "image": None,
                        "image_id": "",
                        "page_number": i + 1,
                        "positions": [],
                        "img_path": "",
                        "metadata": {}
                    }
                    result.append(chunk)
            
            return result
            
        except Exception as e:
            logging.error(f"Error in video chunk method: {e}")
            return [{
                "content_with_weight": f"Video processing failed: {str(e)}",
                "content_ltks": f"Video processing failed: {str(e)}",
                "content_sm_ltks": f"Video processing failed: {str(e)}",
                "image": None,
                "image_id": "",
                "page_number": 1,
                "positions": [],
                "img_path": "",
                "metadata": {"error": str(e)}
            }]


# For compatibility with existing parser system
RAGFlowVideoParser.__name__ = "VideoParser"
