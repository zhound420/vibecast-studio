"""Model manager for lazy-loading VibeVoice models."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal, Tuple, Any
from threading import Lock
import gc


class DeviceType(str, Enum):
    """Supported compute device types."""
    CUDA = "cuda"
    MPS = "mps"
    CPU = "cpu"


@dataclass
class ModelConfig:
    """Configuration for a VibeVoice model."""
    model_id: str
    context_length: int
    max_duration_minutes: int
    max_speakers: int
    vram_requirement_gb: float


# Available model configurations
MODELS = {
    "large": ModelConfig(
        model_id="vibevoice-community/VibeVoice-1.5B",
        context_length=64000,
        max_duration_minutes=90,
        max_speakers=4,
        vram_requirement_gb=7.5,
    ),
    "realtime": ModelConfig(
        model_id="microsoft/VibeVoice-Realtime-0.5B",
        context_length=8000,
        max_duration_minutes=10,
        max_speakers=1,
        vram_requirement_gb=4.0,
    ),
}


class ModelManager:
    """
    Singleton manager for lazy-loading VibeVoice models.

    Handles model loading, switching, and VRAM management.
    Only one model can be loaded at a time to fit within GPU memory.
    """

    _instance: Optional["ModelManager"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_model_type: Optional[str] = None
        self._model = None
        self._processor = None
        self._load_lock = Lock()
        self._device_type: Optional[DeviceType] = None

    def _detect_device(self) -> Tuple[DeviceType, str, Any]:
        """
        Detect the best available compute device.

        Priority: CUDA → MPS → CPU

        Returns:
            Tuple of (device_type, device_map, torch_dtype)
        """
        import torch

        # CUDA (NVIDIA GPUs)
        if torch.cuda.is_available():
            return DeviceType.CUDA, "auto", torch.bfloat16

        # MPS (Apple Silicon M1/M2/M3)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # MPS limitations:
            # - No bfloat16 support, must use float32
            # - No device_map="auto", model placed on CPU then moved
            return DeviceType.MPS, None, torch.float32

        # CPU fallback
        return DeviceType.CPU, "cpu", torch.float32

    def load_model(
        self,
        model_type: Literal["large", "realtime"],
    ) -> Tuple[Any, Any]:
        """
        Load a model, unloading the current one if different.

        Args:
            model_type: Either "large" for VibeVoice-1.5B or "realtime" for Realtime-0.5B

        Returns:
            Tuple of (model, processor)
        """
        with self._load_lock:
            if self._current_model_type == model_type and self._model is not None:
                return self._model, self._processor

            # Unload current model to free VRAM
            if self._model is not None:
                self._unload_current()

            config = MODELS[model_type]

            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoProcessor

                # Load processor
                self._processor = AutoProcessor.from_pretrained(
                    config.model_id,
                    trust_remote_code=True,
                )

                # Detect best available device
                self._device_type, device_map, torch_dtype = self._detect_device()

                # Load model with appropriate configuration
                load_kwargs = {
                    "torch_dtype": torch_dtype,
                    "trust_remote_code": True,
                }

                if self._device_type == DeviceType.MPS:
                    # MPS: Load to CPU first, then move to MPS device
                    self._model = AutoModelForCausalLM.from_pretrained(
                        config.model_id,
                        **load_kwargs,
                    )
                    self._model = self._model.to("mps")
                else:
                    # CUDA/CPU: Use device_map for automatic placement
                    load_kwargs["device_map"] = device_map
                    self._model = AutoModelForCausalLM.from_pretrained(
                        config.model_id,
                        **load_kwargs,
                    )

                self._current_model_type = model_type
                return self._model, self._processor

            except ImportError as e:
                raise RuntimeError(
                    f"Failed to import required packages: {e}. "
                    "Make sure torch and transformers are installed."
                )
            except Exception as e:
                self._current_model_type = None
                self._model = None
                self._processor = None
                raise RuntimeError(f"Failed to load model {config.model_id}: {e}")

    def _unload_current(self):
        """Unload current model and free VRAM/memory."""
        device_type = self._device_type

        del self._model
        del self._processor
        self._model = None
        self._processor = None
        self._current_model_type = None
        self._device_type = None

        # Force garbage collection
        gc.collect()

        # Clear device-specific cache
        try:
            import torch
            if device_type == DeviceType.CUDA and torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif device_type == DeviceType.MPS:
                # MPS cache clearing (requires macOS 12.3+)
                if hasattr(torch.mps, "empty_cache"):
                    torch.mps.empty_cache()
        except (ImportError, AttributeError):
            pass

    def get_current_model_type(self) -> Optional[str]:
        """Get the currently loaded model type."""
        return self._current_model_type

    def get_config(self, model_type: str) -> ModelConfig:
        """Get configuration for a model type."""
        return MODELS[model_type]

    def is_loaded(self) -> bool:
        """Check if any model is currently loaded."""
        return self._model is not None

    def get_device_type(self) -> Optional[DeviceType]:
        """Get the current device type being used."""
        return self._device_type

    def get_device_info(self) -> dict:
        """Get information about the current compute device."""
        import torch

        device_type, _, _ = self._detect_device()
        info = {
            "device_type": device_type.value,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        }

        if device_type == DeviceType.CUDA:
            info["device_name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        elif device_type == DeviceType.MPS:
            info["device_name"] = "Apple Silicon (MPS)"
            # MPS uses unified memory, no separate VRAM pool

        return info

    def get_memory_usage(self) -> float:
        """Get current GPU/accelerator memory usage in GB."""
        try:
            import torch
            if self._device_type == DeviceType.CUDA and torch.cuda.is_available():
                return torch.cuda.memory_allocated() / (1024 ** 3)
            elif self._device_type == DeviceType.MPS:
                # MPS memory tracking (PyTorch 2.0+)
                if hasattr(torch.mps, "current_allocated_memory"):
                    return torch.mps.current_allocated_memory() / (1024 ** 3)
        except (ImportError, AttributeError):
            pass
        return 0.0

    def get_vram_usage(self) -> float:
        """Get current VRAM usage in GB. Alias for get_memory_usage."""
        return self.get_memory_usage()

    def unload(self):
        """Explicitly unload the current model."""
        with self._load_lock:
            if self._model is not None:
                self._unload_current()
