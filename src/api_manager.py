import requests
import time
import hashlib
import os
import json
from typing import List, Dict, Any, Optional, Tuple


CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_cache.json")


PROVIDER_CONFIG = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "openai",
        "api_key_help": "sk-... from platform.openai.com",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "nvidia",
        "api_key_help": "nvapi-... from build.nvidia.com",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "openrouter",
        "api_key_help": "sk-or-... from openrouter.ai/keys",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "google",
        "api_key_help": "AIza... from aistudio.google.com",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "together",
        "api_key_help": "Bearer token from together.ai",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "mistral",
        "api_key_help": "API Key from mistral.ai",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "deepseek",
        "api_key_help": "sk-... from platform.deepseek.com",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "groq",
        "api_key_help": "gsk_... from console.groq.com",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/messages",
        "logo": "anthropic",
        "api_key_help": "sk-ant-... from console.anthropic.com",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
        "logo": "ollama",
        "api_key_help": "Local Ollama running on port 11434",
    },
}


def _load_cache() -> Dict[str, Any]:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _cache_key(provider: str, api_key: str) -> str:
    h = hashlib.sha256(f"{provider}:{api_key}".encode()).hexdigest()[:16]
    return f"{provider}:{h}"


def get_available_models(api_keys: dict) -> list:
    """Returns a list of models available across all connected providers."""
    available = []
    
    # Defaults
    defaults = {
        "openai": [
            {"id": "gpt-4o", "provider": "openai", "display_name": "GPT-4o"},
            {"id": "gpt-4o-mini", "provider": "openai", "display_name": "GPT-4o Mini"},
        ],
        "google": [
            {"id": "gemini-1.5-pro", "provider": "google", "display_name": "Gemini 1.5 Pro"},
            {"id": "gemini-1.5-flash", "provider": "google", "display_name": "Gemini 1.5 Flash"},
        ],
        "nvidia": [
            {"id": "meta/llama-3.1-70b-instruct", "provider": "nvidia", "display_name": "Llama 3.1 70B"},
            {"id": "meta/llama-3.1-405b-instruct", "provider": "nvidia", "display_name": "Llama 3.1 405B"},
        ],
        "openrouter": [
            {"id": "anthropic/claude-3.5-sonnet", "provider": "openrouter", "display_name": "Claude 3.5 Sonnet"},
            {"id": "meta-llama/llama-3.1-70b-instruct", "provider": "openrouter", "display_name": "Llama 3.1 70B (OR)"},
        ],
        "together": [
            {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "provider": "together", "display_name": "Llama 3.1 70B (Together)"},
        ],
        "mistral": [
            {"id": "mistral-large-latest", "provider": "mistral", "display_name": "Mistral Large"},
            {"id": "open-mixtral-8x22b", "provider": "mistral", "display_name": "Mixtral 8x22B"},
        ],
        "deepseek": [
            {"id": "deepseek-chat", "provider": "deepseek", "display_name": "DeepSeek V3 Chat"},
            {"id": "deepseek-reasoner", "provider": "deepseek", "display_name": "DeepSeek R1 Reasoner"},
        ],
        "groq": [
            {"id": "llama-3.1-70b-versatile", "provider": "groq", "display_name": "Llama 3.1 70B (Groq)"},
            {"id": "llama3-8b-8192", "provider": "groq", "display_name": "Llama 3 8B (Groq)"},
        ],
        "anthropic": [
            {"id": "claude-3-5-sonnet-20241022", "provider": "anthropic", "display_name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-haiku-20240307", "provider": "anthropic", "display_name": "Claude 3 Haiku"},
        ],
        "ollama": [
            {"id": "llama3", "provider": "ollama", "display_name": "Llama 3 (Local)"},
            {"id": "deepseek-coder:6.7b", "provider": "ollama", "display_name": "DeepSeek Coder (Local)"},
        ]
    }
    
    cache = _load_cache()
    
    for prov, key in api_keys.items():
        if not key:
            continue
            
        # Add from cache if exists
        ck = _cache_key(prov, key)
        if ck in cache and cache[ck].get("models"):
            available.extend(cache[ck]["models"][:10]) # Top 10 cached
        elif prov in defaults:
            available.extend(defaults[prov])
            
    # Deduplicate by ID
    seen = set()
    deduped = []
    for m in available:
        if m["id"] not in seen:
            seen.add(m["id"])
            deduped.append(m)
            
    return deduped


def fetch_models(provider: str, api_key: str, force_refresh: bool = False) -> list:
    if provider not in PROVIDER_CONFIG:
        return []

    cache = _load_cache()
    ck = _cache_key(provider, api_key)

    if not force_refresh and ck in cache:
        return cache[ck]["models"]

    cfg = PROVIDER_CONFIG[provider]
    base = cfg["base_url"].rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    models = []

    if provider == "google":
        try:
            r = requests.get(f"{base}/models?key={api_key}", timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "data" in data:
                    for m in data["data"]:
                        mid = m.get("id", "")
                        if mid and "generateContent" in m.get("capabilities", {}).get("generation", False):
                            models.append({"id": mid, "name": mid, "provider": provider, "display_name": mid})
                elif "models" in data:
                    for m in data["models"]:
                        name = m.get("name", "").replace("models/", "")
                        if "gemini" in name.lower() and "generateContent" in m.get("supportedGenerationMethods", []):
                            models.append({"id": name, "name": name, "provider": provider, "display_name": name})
            else:
                models = _fallback_models(provider)
        except Exception:
            models = _fallback_models(provider)
        except Exception:
            models = _fallback_models(provider)
    elif provider == "anthropic":
        # Anthropic doesn't have a simple /models list in the same way, we just use defaults
        models = _fallback_models(provider)
    else:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}" if provider != "ollama" else "",
                "Content-Type": "application/json",
            }
            if provider == "ollama" and not api_key:
                headers = {"Content-Type": "application/json"}
            
            r = requests.get(f"{base}{cfg['models_endpoint']}", headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                model_list = data.get("data", data.get("models", []))
                for m in model_list:
                    mid = m.get("id", m.get("name", ""))
                    if mid and mid != "string":
                        models.append({"id": mid, "name": mid, "provider": provider, "display_name": m.get("display_name", mid)})
            else:
                models = _fallback_models(provider)
        except Exception:
            models = _fallback_models(provider)

    cache[ck] = {"models": models, "fetched_at": time.time()}
    _save_cache(cache)
    return models


def _fallback_models(provider: str) -> List[Dict[str, str]]:
    fallbacks = {
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "display_name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "display_name": "GPT-4o Mini"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "display_name": "GPT-3.5 Turbo"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai", "display_name": "GPT-4 Turbo"},
        ],
        "nvidia": [
            {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "Llama 3.1 Nemotron 70B", "provider": "nvidia", "display_name": "Nemotron 70B"},
            {"id": "nvidia/mistral-nemo-12b-instruct", "name": "Mistral Nemo 12B", "provider": "nvidia", "display_name": "Mistral Nemo 12B"},
            {"id": "nvidia/nemotron-mini-4b", "name": "Nemotron Mini 4B", "provider": "nvidia", "display_name": "Nemotron Mini 4B"},
        ],
        "openrouter": [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "openrouter", "display_name": "GPT-4o"},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "openrouter", "display_name": "Claude 3.5 Sonnet"},
            {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "provider": "openrouter", "display_name": "Gemini 2.0 Flash"},
            {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B", "provider": "openrouter", "display_name": "Llama 3.3 70B"},
        ],
        "google": [
            {"id": "google/gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google", "display_name": "Gemini 2.0 Flash"},
            {"id": "google/gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "display_name": "Gemini 1.5 Pro"},
        ],
        "together": [
            {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "name": "Llama 3.1 70B (Together)", "provider": "together", "display_name": "Llama 3.1 70B (Together)"},
        ],
        "mistral": [
            {"id": "mistral-large-latest", "name": "Mistral Large", "provider": "mistral", "display_name": "Mistral Large"},
        ],
        "deepseek": [
            {"id": "deepseek-chat", "name": "DeepSeek V3 Chat", "provider": "deepseek", "display_name": "DeepSeek V3 Chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek R1 Reasoner", "provider": "deepseek", "display_name": "DeepSeek R1 Reasoner"},
        ],
        "groq": [
            {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "provider": "groq", "display_name": "Llama 3.1 70B (Groq)"},
        ],
        "anthropic": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "display_name": "Claude 3.5 Sonnet"},
        ],
        "ollama": [
            {"id": "llama3", "name": "Llama 3", "provider": "ollama", "display_name": "Llama 3 (Local)"},
        ],
    }
    return fallbacks.get(provider, [])


def chat_completion(
    provider: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 10,
    timeout: int = 30,
) -> Tuple[Optional[str], Dict[str, Any]]:
    stats = {"tokens_in": 0, "tokens_out": 0, "latency_ms": 0, "error": None, "status_code": 0}

    if provider not in PROVIDER_CONFIG:
        stats["error"] = f"Unknown provider: {provider}"
        return None, stats

    cfg = PROVIDER_CONFIG[provider]
    base = cfg["base_url"].rstrip("/")
    uri = f"{base}{cfg['chat_endpoint']}"
    if provider == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Anthropic doesn't use the standard system message format, but newer Messages API supports system parameter
        sys_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system": sys_msg += m["content"] + "\n"
            else: user_msgs.append({"role": "user", "content": m["content"]})
            
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": sys_msg.strip(),
            "messages": user_msgs
        }
    else:
        headers = {
            "Authorization": f"Bearer {api_key}" if provider != "ollama" else "",
            "Content-Type": "application/json",
        }
        if provider == "ollama" and not api_key:
            headers = {"Content-Type": "application/json"}
            
        payload = {
            "model": model.replace(f"{provider}/", ""),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    t0 = time.time()
    try:
        r = requests.post(uri, headers=headers, json=payload, timeout=timeout)
        stats["status_code"] = r.status_code
        stats["latency_ms"] = int((time.time() - t0) * 1000)

        if r.status_code == 200:
            data = r.json()
            if provider == "anthropic":
                usage = data.get("usage", {})
                stats["tokens_in"] = usage.get("input_tokens", 0)
                stats["tokens_out"] = usage.get("output_tokens", 0)
                content = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                content = content.strip()
            else:
                usage = data.get("usage", {})
                stats["tokens_in"] = usage.get("prompt_tokens", 0)
                stats["tokens_out"] = usage.get("completion_tokens", 0)
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return content, stats
        else:
            stats["error"] = f"HTTP {r.status_code}: {r.text[:300]}"
            return None, stats
    except requests.exceptions.Timeout:
        stats["error"] = "Timeout"
        stats["latency_ms"] = int((time.time() - t0) * 1000)
        return None, stats
    except Exception as e:
        stats["error"] = str(e)
        stats["latency_ms"] = int((time.time() - t0) * 1000)
        return None, stats