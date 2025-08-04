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
import tempfile
import os
import logging

from api.db import LLMType
from rag.nlp import rag_tokenizer
from api.db.services.llm_service import LLMBundle
from rag.nlp import tokenize, tokenize_chunks
from deepdoc.parser.txt_parser import RAGFlowTxtParser

def chunk(filename, binary, tenant_id, lang, callback=None, **kwargs):
    doc = {
        "docnm_kwd": filename,
        "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename))
    }
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])

    # is it English
    eng = lang.lower() == "english"
    
    # Get parser configuration from kwargs
    parser_config = kwargs.get("parser_config", {})
    chunk_token_num = int(parser_config.get("chunk_token_num", 512))
    delimiter = parser_config.get("delimiter", "\n!?;。；！？")
    
    # Try to use SPEECH2TEXT LLM first
    try:
        callback(0.1, "Attempting to use SPEECH2TEXT LLM to transcribe the audio")
        seq2txt_mdl = LLMBundle(tenant_id, LLMType.SPEECH2TEXT, lang=lang)
        ans = seq2txt_mdl.transcription(binary)
        callback(0.8, "SPEECH2TEXT LLM respond: %s ..." % ans[:32])
        
        # Split transcription into chunks based on configuration
        if len(ans.strip()) == 0:
            callback(prog=-1, msg="Audio transcription returned empty text")
            return []
            
        callback(0.85, "Splitting transcription into chunks...")
        chunks = RAGFlowTxtParser.parser_txt(ans, chunk_token_num, delimiter)
        
        # Convert chunks to documents
        res = []
        for i, (chunk_text, _) in enumerate(chunks):
            if len(chunk_text.strip()) == 0:
                continue
            chunk_doc = doc.copy()
            tokenize(chunk_doc, chunk_text, eng)
            chunk_doc["chunk_id"] = i
            res.append(chunk_doc)
        
        callback(0.9, f"Created {len(res)} chunks from audio transcription")
        return res
        
    except Exception as e:
        # If SPEECH2TEXT model is not configured, try fallback to Whisper
        callback(0.2, f"SPEECH2TEXT model not available ({str(e)}), falling back to Whisper...")
        
        try:
            # Import whisper as fallback
            import whisper
            callback(0.3, "Loading Whisper model for audio transcription...")
            
            # Save binary audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(binary)
                temp_audio_path = temp_file.name
            
            try:
                # Load Whisper model
                model = whisper.load_model("base")
                
                callback(0.5, "Transcribing audio with Whisper...")
                
                # Transcribe with Whisper
                result = model.transcribe(temp_audio_path, language=None, verbose=False)
                
                if result and result.get("text"):
                    ans = result["text"].strip()
                    callback(0.8, f"Whisper transcription completed: {ans[:50]}...")
                    
                    # Split transcription into chunks based on configuration
                    callback(0.85, "Splitting transcription into chunks...")
                    chunks = RAGFlowTxtParser.parser_txt(ans, chunk_token_num, delimiter)
                    
                    # Convert chunks to documents
                    res = []
                    for i, (chunk_text, _) in enumerate(chunks):
                        if len(chunk_text.strip()) == 0:
                            continue
                        chunk_doc = doc.copy()
                        tokenize(chunk_doc, chunk_text, eng)
                        chunk_doc["chunk_id"] = i
                        res.append(chunk_doc)
                    
                    callback(0.9, f"Created {len(res)} chunks from audio transcription")
                    return res
                else:
                    callback(prog=-1, msg="Whisper transcription failed: No text detected")
                    return []
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                    
        except ImportError:
            callback(prog=-1, msg="No audio transcription available. Please either:\n1. Configure a SPEECH2TEXT model in System Settings > Model Providers, OR\n2. Install Whisper with: pip install openai-whisper")
            return []
        except Exception as whisper_error:
            callback(prog=-1, msg=f"Audio transcription failed with both SPEECH2TEXT and Whisper. Error: {str(whisper_error)}")
            return []

    return []
