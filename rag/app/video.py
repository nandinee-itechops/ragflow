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

import re
import json
import logging
import os
from typing import List, Dict, Any, Optional

from api.db import LLMType
from rag.nlp import rag_tokenizer
from api.db.services.llm_service import LLMBundle
from rag.nlp import tokenize
from deepdoc.parser.video_parser import RAGFlowVideoParser


def chunk(filename, binary, tenant_id, lang, callback=None, **kwargs):
    """
    Process video file and create chunks with temporal information.
    
    Args:
        filename: Video filename
        binary: Video binary data
        tenant_id: Tenant ID for LLM access
        lang: Language setting
        callback: Progress callback function
        **kwargs: Additional processing options
        
    Returns:
        List of processed document chunks
    """
    docs = []
    
    try:
        # Initialize document metadata
        doc_base = {
            "docnm_kwd": filename,
            "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z0-9]+$", "", filename))
        }
        doc_base["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc_base["title_tks"])
        
        # Check language setting
        eng = lang.lower() == "english"
        
        if callback:
            callback(0.05, "Initializing video processing...")
        
        # Get available models
        vision_model = None
        speech_model = None
        
        try:
            # Try to get vision model for frame analysis
            vision_bundle = LLMBundle(tenant_id, LLMType.IMAGE2TEXT, lang=lang)
            vision_model = vision_bundle.mdl
            if callback:
                callback(0.1, "Vision model loaded for frame analysis")
        except Exception as e:
            logging.warning(f"Could not load vision model: {e}")
            vision_model = None
            if callback:
                callback(0.1, "Warning: No vision model available for frame analysis")
        
        try:
            # Try to get speech-to-text model for audio transcription
            speech_bundle = LLMBundle(tenant_id, LLMType.SPEECH2TEXT, lang=lang)
            speech_model = speech_bundle
            if callback:
                callback(0.15, "Speech-to-text model loaded for audio transcription")
        except Exception as e:
            logging.warning(f"Could not load speech model: {e}")
            speech_model = None
            if callback:
                callback(0.15, "Warning: No speech-to-text model available for audio transcription")
        
        # Check if we have at least one processing model
        if not vision_model and not speech_model:
            # If no AI models available, we can still extract basic frame metadata
            logging.info("No AI models available, will use basic video processing")
            vision_model = None
            speech_model = None
            if callback:
                callback(0.15, "Using basic video processing (no AI models available)")
        
        # Initialize video parser with available models
        parser_kwargs = {
            'vision_model': vision_model,
            'speech_model': speech_model,
            'frame_interval': kwargs.get('frame_interval', 5.0),
            'audio_chunk_duration': kwargs.get('audio_chunk_duration', 30.0),
            'max_frames': kwargs.get('max_frames', 100)
        }
        
        video_parser = RAGFlowVideoParser(**parser_kwargs)
        
        if callback:
            callback(0.2, "Starting video processing...")
        
        # Create temporary file for video processing if binary data is provided
        temp_video_path = None
        try:
            if isinstance(binary, bytes):
                # Save binary data to temporary file
                import tempfile
                # Use appropriate file extension based on filename
                file_ext = '.mp4'  # Default
                if isinstance(filename, str) and '.' in filename:
                    file_ext = os.path.splitext(filename)[1] or '.mp4'
                
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(binary)
                    temp_video_path = temp_file.name
                
                # Process video from temporary file
                chunks, _ = video_parser(
                    filename=temp_video_path,
                    from_page=kwargs.get('from_time', 0),
                    to_page=kwargs.get('to_time', 100000),
                    callback=callback
                )
            else:
                # If filename is provided as string, use it directly
                chunks, _ = video_parser(
                    filename=filename,
                    from_page=kwargs.get('from_time', 0),
                    to_page=kwargs.get('to_time', 100000),
                    callback=callback
                )
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except:
                    pass
        
        if not chunks:
            logging.warning("No chunks extracted from video")
            if callback:
                callback(-1, "No content could be extracted from video. Please check:\n1. Video file is valid\n2. FFmpeg is installed\n3. Whisper is available (pip install openai-whisper)")
            return []
        
        if callback:
            callback(0.95, f"Processing {len(chunks)} video segments...")
        
        # Process each chunk and create documents
        for i, (chunk_text, metadata_str) in enumerate(chunks):
            try:
                # Parse metadata
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                # Create document for this chunk
                doc = doc_base.copy()
                
                # Add temporal metadata
                doc.update({
                    "chunk_index": i,
                    "start_time": metadata.get('start_time', 0),
                    "end_time": metadata.get('end_time', 0),
                    "has_audio": metadata.get('has_audio', False),
                    "has_video": metadata.get('has_video', False),
                    "frame_count": metadata.get('frame_count', 0),
                    "content_type": "video"
                })
                
                # Tokenize the chunk text
                tokenize(doc, chunk_text, eng)
                
                # Add temporal keywords for better searchability
                temporal_keywords = []
                start_time = metadata.get('start_time', 0)
                end_time = metadata.get('end_time', 0)
                
                # Add time-based keywords
                minutes_start = int(start_time // 60)
                minutes_end = int(end_time // 60)
                temporal_keywords.extend([
                    f"minute_{minutes_start}",
                    f"time_{int(start_time)}s",
                    f"duration_{int(end_time - start_time)}s"
                ])
                
                # Add content type keywords
                if metadata.get('has_audio'):
                    temporal_keywords.append("with_audio")
                if metadata.get('has_video'):
                    temporal_keywords.append("with_video")
                
                # Merge temporal keywords with existing keywords
                if 'keywords' in doc:
                    doc['keywords'].extend(temporal_keywords)
                else:
                    doc['keywords'] = temporal_keywords
                
                docs.append(doc)
                
            except Exception as chunk_error:
                logging.error(f"Error processing chunk {i}: {chunk_error}")
                continue
        
        if callback:
            callback(1.0, f"Video processing completed. Generated {len(docs)} chunks.")
        
        return docs
        
    except Exception as e:
        error_msg = f"Error processing video: {str(e)}"
        logging.error(error_msg)
        if callback:
            callback(-1, error_msg)
        return []


def get_video_duration(binary: bytes) -> float:
    """
    Get video duration in seconds.
    
    Args:
        binary: Video binary data
        
    Returns:
        Duration in seconds
    """
    try:
        return float(RAGFlowVideoParser.total_page_number("", binary))
    except Exception as e:
        logging.error(f"Error getting video duration: {e}")
        return 0.0


def extract_temporal_info(chunk_text: str) -> Dict[str, Any]:
    """
    Extract temporal information from chunk text.
    
    Args:
        chunk_text: Text content of the chunk
        
    Returns:
        Dictionary with temporal information
    """
    try:
        # Extract timestamp information
        timestamp_match = re.search(r'\[Time: (\d+\.?\d*)s - (\d+\.?\d*)s\]', chunk_text)
        if timestamp_match:
            start_time = float(timestamp_match.group(1))
            end_time = float(timestamp_match.group(2))
            
            return {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'start_minute': int(start_time // 60),
                'end_minute': int(end_time // 60)
            }
    except Exception as e:
        logging.warning(f"Error extracting temporal info: {e}")
    
    return {}


def format_video_chunk_for_retrieval(chunk_text: str, metadata: Dict[str, Any] = None) -> str:
    """
    Format video chunk for better retrieval and display.
    
    Args:
        chunk_text: Original chunk text
        metadata: Optional metadata dictionary
        
    Returns:
        Formatted text for display
    """
    try:
        # Extract temporal info from text if not in metadata
        if not metadata:
            metadata = extract_temporal_info(chunk_text)
        
        # Clean up the chunk text
        clean_text = RAGFlowVideoParser.remove_tag(chunk_text)
        
        # Add formatted timestamp header if temporal info available
        if 'start_time' in metadata and 'end_time' in metadata:
            start_time = metadata['start_time']
            end_time = metadata['end_time']
            
            # Format time as MM:SS
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)
            
            time_header = f"🎬 Video Segment ({start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d})"
            return f"{time_header}\n\n{clean_text}"
        
        return clean_text
        
    except Exception as e:
        logging.warning(f"Error formatting video chunk: {e}")
        return chunk_text


# Export functions for use in other modules
__all__ = [
    'chunk',
    'get_video_duration', 
    'extract_temporal_info',
    'format_video_chunk_for_retrieval'
]
