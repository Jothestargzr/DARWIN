"""
GLM-5 Series Python Client & Inference Module
Supports GLM-5.2, GLM-5.1, and GLM-5 via Z.ai Global API, OpenRouter / OpenAI-compatible proxies, ZhipuAI, or Hugging Face Transformers.
"""

import os
from typing import Dict, List, Optional, Any, Generator, Union
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False


class GLM5Client:
    """
    Unified client for GLM-5 series models (GLM-5.2, GLM-5.1, GLM-5).
    Supports international routing (Z.ai Global, OpenRouter, Custom Proxies).
    """

    SUPPORTED_MODELS = ["glm-5.2", "glm-5.1", "glm-5", "glm-4-flash"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "glm-5.2",
        use_openai_sdk: bool = True
    ):
        """
        Initialize GLM-5 Client with flexible routing and token support.
        
        :param api_key: API token (checks ZAI_API_KEY, OPENAI_API_KEY, GLM_API_KEY, ZHIPU_API_KEY)
        :param base_url: Custom API endpoint (e.g. 'https://api.z.ai/v1', 'https://openrouter.ai/api/v1', or custom proxy)
        :param default_model: Default model to use (default: "glm-5.2")
        :param use_openai_sdk: Set to True to use standard OpenAI-compatible client
        """
        # Resolve API token from multiple possible env variables
        self.api_key = (
            api_key
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("ZAI_API_KEY")
            or os.getenv("GLM_API_KEY")
            or os.getenv("ZHIPU_API_KEY")
        )

        # Resolve Base URL (defaults to OpenRouter if OPENROUTER_API_KEY present or base_url given)
        default_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else "https://api.z.ai/v1"
        self.base_url = (
            base_url
            or os.getenv("GLM_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("ZAI_BASE_URL")
            or default_url
        )

        self.default_model = os.getenv("GLM_DEFAULT_MODEL", default_model)
        self.use_openai_sdk = use_openai_sdk

        if not self.api_key:
            self.client = None
        elif self.base_url or use_openai_sdk or not ZHIPUAI_AVAILABLE:
            if not OPENAI_AVAILABLE:
                raise ImportError("The 'openai' python package is required for custom API routing. Run: pip install openai")
            
            # Default to Z.ai global API if base_url is omitted but using OpenAI client
            target_base_url = self.base_url or "https://api.z.ai/v1"
            
            headers = {
                "HTTP-Referer": "https://github.com/zai-org/GLM-5",
                "X-Title": "GLM-5 CLI Client"
            }
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=target_base_url,
                default_headers=headers
            )
            self.is_openai_backend = True
        else:
            self.client = ZhipuAI(api_key=self.api_key)
            self.is_openai_backend = False

    def is_configured(self) -> bool:
        """Check if client has a valid API key configured."""
        placeholder_keys = ["your_zhipu_api_key_here", "your_api_token_here", "your_zai_api_key_here"]
        return bool(self.api_key and self.api_key not in placeholder_keys)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
        extra_kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a non-streaming chat completion request to GLM-5.
        """
        if not self.is_configured():
            raise ValueError(
                "No valid API token configured. Please set ZAI_API_KEY, OPENAI_API_KEY, or GLM_API_KEY in your .env file."
            )

        selected_model = model or self.default_model
        params = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        # Apply GLM-5 specific reasoning effort parameters
        effort = reasoning_effort or os.getenv("GLM_REASONING_EFFORT", "max")
        if effort in ["max", "high"]:
            params["reasoning_effort"] = effort

        if enable_thinking is not None:
            params["enable_thinking"] = enable_thinking

        if tools:
            params["tools"] = tools

        if extra_kwargs:
            params.update(extra_kwargs)

        response = self.client.chat.completions.create(**params)
        
        content = response.choices[0].message.content
        role = response.choices[0].message.role
        model_name = getattr(response, "model", selected_model)

        return {
            "content": content,
            "role": role,
            "model": model_name,
            "raw": response
        }

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        extra_kwargs: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Send a streaming chat completion request to GLM-5.
        """
        if not self.is_configured():
            raise ValueError(
                "No valid API token configured. Please set ZAI_API_KEY, OPENAI_API_KEY, or GLM_API_KEY in your .env file."
            )

        selected_model = model or self.default_model
        params = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True
        }

        effort = reasoning_effort or os.getenv("GLM_REASONING_EFFORT", "max")
        if effort in ["max", "high"]:
            params["reasoning_effort"] = effort

        if enable_thinking is not None:
            params["enable_thinking"] = enable_thinking

        if extra_kwargs:
            params.update(extra_kwargs)

        response = self.client.chat.completions.create(**params)
        for chunk in response:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    yield delta.content


def load_local_glm5_model(
    model_path: str = "zai-org/GLM-5.2",
    device_map: str = "auto",
    torch_dtype: str = "bfloat16"
):
    """
    Utility function to load GLM-5 locally using Hugging Face Transformers.
    Note: Requires GPU hardware capable of handling model weights.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Loading tokenizer for {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    dtype_map = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32
    }
    dtype = dtype_map.get(torch_dtype, torch.bfloat16)

    print(f"Loading local GLM-5 model from {model_path} (dtype={torch_dtype})...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        device_map=device_map,
        torch_dtype=dtype
    )
    return model, tokenizer
