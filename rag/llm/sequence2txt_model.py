#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
import base64
import io
import json
import os
import re
from abc import ABC
from urllib.parse import urljoin

import requests
from openai import OpenAI
from openai.lib.azure import AzureOpenAI

from rag.utils import num_tokens_from_string


class Base(ABC):
    def __init__(self, key, model_name):
        pass

    def transcription(self, audio, **kwargs):
        transcription = self.client.audio.transcriptions.create(model=self.model_name, file=audio, response_format="text")
        return transcription.text.strip(), num_tokens_from_string(transcription.text.strip())

    def audio2base64(self, audio):
        if isinstance(audio, bytes):
            return base64.b64encode(audio).decode("utf-8")
        if isinstance(audio, io.BytesIO):
            return base64.b64encode(audio.getvalue()).decode("utf-8")
        raise TypeError("The input audio file should be in binary format.")


class GPTSeq2txt(Base):
    _FACTORY_NAME = "OpenAI"

    def __init__(self, key, model_name="whisper-1", base_url="https://api.openai.com/v1"):
        if not base_url:
            base_url = "https://api.openai.com/v1"
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.model_name = model_name


class QWenSeq2txt(Base):
    _FACTORY_NAME = "Tongyi-Qianwen"

    def __init__(self, key, model_name="paraformer-realtime-8k-v1", **kwargs):
        import dashscope

        dashscope.api_key = key
        self.model_name = model_name

    def transcription(self, audio, format):
        from http import HTTPStatus

        from dashscope.audio.asr import Recognition

        recognition = Recognition(model=self.model_name, format=format, sample_rate=16000, callback=None)
        result = recognition.call(audio)

        ans = ""
        if result.status_code == HTTPStatus.OK:
            for sentence in result.get_sentence():
                ans += sentence.text.decode("utf-8") + "\n"
            return ans, num_tokens_from_string(ans)

        return "**ERROR**: " + result.message, 0


class AzureSeq2txt(Base):
    _FACTORY_NAME = "Azure-OpenAI"

    def __init__(self, key, model_name, lang="Chinese", **kwargs):
        self.client = AzureOpenAI(api_key=key, azure_endpoint=kwargs["base_url"], api_version="2024-02-01")
        self.model_name = model_name
        self.lang = lang


class XinferenceSeq2txt(Base):
    _FACTORY_NAME = "Xinference"

    def __init__(self, key, model_name="whisper-small", **kwargs):
        self.base_url = kwargs.get("base_url", "http://127.0.0.1:9997").rstrip('/')
        self.model_name = model_name
        self.key = key
        self.model_uid = None
        self.xinference_client = None
        
        # Initialize Xinference client and find model
        try:
            from xinference.client import Client
            self.xinference_client = Client(self.base_url)
            
            # Find the correct model UID
            models = self.xinference_client.list_models()
            for model in models:
                model_name_in_list = model.get('model_name', '')
                model_uid_in_list = model.get('model_uid', '')
                model_type = model.get('model_type', '')
                
                # Match by model name and ensure it's an audio model
                if (model_name_in_list == self.model_name and 
                    model_type == 'audio'):
                    self.model_uid = model_uid_in_list
                    break
                    
            # If exact match not found, try any whisper audio model
            if not self.model_uid:
                for model in models:
                    model_name_in_list = model.get('model_name', '')
                    model_type = model.get('model_type', '')
                    
                    if ('whisper' in model_name_in_list.lower() and 
                        model_type == 'audio'):
                        self.model_uid = model.get('model_uid')
                        break
                        
        except Exception as e:
            print(f"Warning: Could not initialize Xinference client: {e}")
            
        # Set up OpenAI-compatible client using urljoin like other Xinference classes
        base_url = urljoin(self.base_url, "v1")
        self.client = OpenAI(
            api_key=self.key or "empty",
            base_url=base_url
        )

    def transcription(self, audio, language="en", prompt=None, response_format="text", temperature=0.0):
        try:
            # Handle different audio input types
            if isinstance(audio, str):
                # File path
                with open(audio, "rb") as f:
                    audio_data = io.BytesIO(f.read())
                    audio_data.name = os.path.basename(audio)
            elif isinstance(audio, bytes):
                # Raw bytes
                audio_data = io.BytesIO(audio)
                audio_data.name = "audio.wav"
            elif hasattr(audio, 'read'):
                # File-like object
                audio_data = audio
                if not hasattr(audio_data, 'name'):
                    audio_data.name = "audio.wav"
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")

            # Use the model UID if available, otherwise use model name
            model_to_use = self.model_uid if self.model_uid else self.model_name
            
            # Call OpenAI-compatible API
            result = self.client.audio.transcriptions.create(
                model=model_to_use,
                file=audio_data,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature
            )
            
            # Handle response based on format
            if response_format == "text":
                transcription_text = result.strip() if isinstance(result, str) else str(result).strip()
            else:
                transcription_text = result.text.strip() if hasattr(result, 'text') else str(result).strip()
            
            return transcription_text, num_tokens_from_string(transcription_text)
            
        except Exception as e:
            error_msg = f"**ERROR**: {str(e)}"
            return error_msg, 0


class TencentCloudSeq2txt(Base):
    _FACTORY_NAME = "Tencent Cloud"

    def __init__(self, key, model_name="16k_zh", base_url="https://asr.tencentcloudapi.com"):
        from tencentcloud.asr.v20190614 import asr_client
        from tencentcloud.common import credential

        key = json.loads(key)
        sid = key.get("tencent_cloud_sid", "")
        sk = key.get("tencent_cloud_sk", "")
        cred = credential.Credential(sid, sk)
        self.client = asr_client.AsrClient(cred, "")
        self.model_name = model_name

    def transcription(self, audio, max_retries=60, retry_interval=5):
        import time

        from tencentcloud.asr.v20190614 import models
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
            TencentCloudSDKException,
        )

        b64 = self.audio2base64(audio)
        try:
            # dispatch disk
            req = models.CreateRecTaskRequest()
            params = {
                "EngineModelType": self.model_name,
                "ChannelNum": 1,
                "ResTextFormat": 0,
                "SourceType": 1,
                "Data": b64,
            }
            req.from_json_string(json.dumps(params))
            resp = self.client.CreateRecTask(req)

            # loop query
            req = models.DescribeTaskStatusRequest()
            params = {"TaskId": resp.Data.TaskId}
            req.from_json_string(json.dumps(params))
            retries = 0
            while retries < max_retries:
                resp = self.client.DescribeTaskStatus(req)
                if resp.Data.StatusStr == "success":
                    text = re.sub(r"\[\d+:\d+\.\d+,\d+:\d+\.\d+\]\s*", "", resp.Data.Result).strip()
                    return text, num_tokens_from_string(text)
                elif resp.Data.StatusStr == "failed":
                    return (
                        "**ERROR**: Failed to retrieve speech recognition results.",
                        0,
                    )
                else:
                    time.sleep(retry_interval)
                    retries += 1
            return "**ERROR**: Max retries exceeded. Task may still be processing.", 0

        except TencentCloudSDKException as e:
            return "**ERROR**: " + str(e), 0
        except Exception as e:
            return "**ERROR**: " + str(e), 0


class GPUStackSeq2txt(Base):
    _FACTORY_NAME = "GPUStack"

    def __init__(self, key, model_name, base_url):
        if not base_url:
            raise ValueError("url cannot be None")
        if base_url.split("/")[-1] != "v1":
            base_url = os.path.join(base_url, "v1")
        self.base_url = base_url
        self.model_name = model_name
        self.key = key


class GiteeSeq2txt(Base):
    _FACTORY_NAME = "GiteeAI"

    def __init__(self, key, model_name="whisper-1", base_url="https://ai.gitee.com/v1/"):
        if not base_url:
            base_url = "https://ai.gitee.com/v1/"
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.model_name = model_name

