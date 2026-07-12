"""GPU detection, VRAM tiering, and model recommendation for local LLM onboarding.

Canonical implementation. Mirrored in mcp-central-docs/templates/llm-detect/
for fleet reuse — update both when changing the tier table.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("godot-mcp.llm-detect")

# VRAM in MB -> (tier, label, models in priority order)
# Models checked against what Ollama actually has installed.
TIERS: list[tuple[int, int, str, list[str]]] = [
    (32000, 5, "Monster", ["qwen2.5-coder:32b-instruct-q4_K_M", "deepseek-r1:32b", "gemma4:26b"]),
    (20000, 4, "High-end", ["gemma4:12b", "qwen2.5-coder:14b", "llama3.1:8b"]),
    (14000, 3, "Mid", ["qwen2.5-coder:7b", "mistral:7b", "llama3.2:3b"]),
    (10000, 2, "Entry", ["llama3.2:3b", "qwen2.5-coder:1.5b"]),
    (6000, 1, "Minimal", ["llama3.2:1b", "tinyllama:latest", "gemma3:1b"]),
]

CLOUD_DEFAULTS = {
    "provider": "deepseek",
    "model": "deepseek-v4-flash",
    "base_url": "https://api.deepseek.com/v1",
    "cost_per_mtok": 0.15,
    "note": "Cheap, fast, good-enough for game generation",
}


@dataclass
class GpuInfo:
    available: bool = False
    name: str = ""
    vram_mb: int = 0
    vram_gb: float = 0.0
    driver: str = ""

    @property
    def tier(self) -> int:
        if not self.available:
            return 0
        for min_vram, tier, _label, _models in TIERS:
            if self.vram_mb >= min_vram:
                return tier
        return 0

    @property
    def tier_label(self) -> str:
        for min_vram, _tier, label, _models in TIERS:
            if self.vram_mb >= min_vram:
                return label
        return "Cloud-only"

    @property
    def recommended_models(self) -> list[str]:
        for min_vram, _tier, _label, models in TIERS:
            if self.vram_mb >= min_vram:
                return models
        return []


@dataclass
class OllamaInfo:
    available: bool = False
    url: str = "http://localhost:11434"
    models: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class DetectResult:
    gpu: GpuInfo = field(default_factory=GpuInfo)
    ollama: OllamaInfo = field(default_factory=OllamaInfo)
    mode: str = "local"  # "local" | "cloud" | "none"


@dataclass
class RecommendResult:
    mode: str = "local"
    tier: int = 0
    tier_label: str = ""
    vram_gb: float = 0.0
    model: str = ""
    installed: bool = False
    cloud_fallback: dict[str, Any] = field(default_factory=lambda: dict(CLOUD_DEFAULTS))
    message: str = ""


def detect_gpu() -> GpuInfo:
    """Probe NVIDIA GPU via nvidia-smi. No external deps needed."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return GpuInfo()
        parts = [p.strip() for p in out.stdout.strip().split(", ")]
        vram = int(parts[1])
        return GpuInfo(
            available=True,
            name=parts[0],
            vram_mb=vram,
            vram_gb=round(vram / 1024, 1),
            driver=parts[2] if len(parts) > 2 else "",
        )
    except FileNotFoundError:
        logger.debug("nvidia-smi not found — no NVIDIA driver")
        return GpuInfo()
    except (ValueError, IndexError, subprocess.TimeoutExpired) as e:
        logger.debug("GPU detection failed: %s", e)
        return GpuInfo()


def check_ollama(url: str = "http://localhost:11434") -> OllamaInfo:
    """Check if Ollama is running and list installed models."""
    import json as _json
    import urllib.request

    try:
        resp = urllib.request.urlopen(f"{url}/api/tags", timeout=3)
        data = _json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        return OllamaInfo(available=True, url=url, models=models)
    except Exception as e:
        return OllamaInfo(error=str(e))


def detect() -> DetectResult:
    """Full detection: GPU + Ollama, returns structured result."""
    gpu = detect_gpu()
    ollama = check_ollama()
    if gpu.available or ollama.available:
        mode = "local"
    else:
        mode = "cloud"
    return DetectResult(gpu=gpu, ollama=ollama, mode=mode)


def recommend(result: DetectResult | None = None) -> RecommendResult:
    """Pick the best model given what's detected and what's installed."""
    if result is None:
        result = detect()

    out = RecommendResult(
        mode=result.mode,
        cloud_fallback=dict(CLOUD_DEFAULTS),
    )

    if not result.gpu.available and not result.ollama.available:
        out.mode = "cloud"
        out.message = f"No local GPU or Ollama found. Configure {CLOUD_DEFAULTS['provider']} API key."
        return out

    if result.ollama.available and result.ollama.models:
        # Check installed models first
        installed_set = set(result.ollama.models)
        for tier_entry in TIERS:
            _min_vram, tier_num, label, models = tier_entry
            if result.gpu.available and result.gpu.vram_mb < _min_vram:
                continue
            for m in models:
                if m in installed_set:
                    out.tier = tier_num
                    out.tier_label = label
                    out.model = m
                    out.installed = True
                    out.vram_gb = result.gpu.vram_gb
                    out.message = f"Using installed model {m} ({label})"
                    return out

    # GPU detected but no matching model installed — recommend the best fit
    if result.gpu.available:
        for min_vram, tier_num, label, models in TIERS:
            if result.gpu.vram_mb >= min_vram:
                out.tier = tier_num
                out.tier_label = label
                out.model = models[0]
                out.vram_gb = result.gpu.vram_gb
                install_cmd = f"ollama pull {models[0]}"
                out.message = f"GPU {result.gpu.name} ({result.gpu.vram_gb} GB). Pull model: {install_cmd}"
                return out

    # Ollama available but no GPU detected — pick smallest model
    if result.ollama.available:
        models = TIERS[-1][3]  # lowest tier
        for m in models:
            if m in set(result.ollama.models):
                out.tier = 1
                out.tier_label = "Minimal"
                out.model = m
                out.installed = True
                out.message = f"CPU mode using {m}"
                return out
        out.tier = 1
        out.tier_label = "Minimal"
        out.model = models[0]
        out.message = f"CPU mode. Pull model: ollama pull {models[0]}"
        return out

    return out
