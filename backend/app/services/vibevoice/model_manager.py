"""Model manager for lazy-loading VibeVoice models."""

from dataclasses import dataclass
from typing import Optional, Literal, Tuple, Any
from threading import Lock
import gc


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

                # Determine device
                if torch.cuda.is_available():
                    device_map = "auto"
                    torch_dtype = torch.bfloat16
                else:
                    device_map = "cpu"
                    torch_dtype = torch.float32

                # Load model
                self._model = AutoModelForCausalLM.from_pretrained(
                    config.model_id,
                    device_map=device_map,
                    torch_dtype=torch_dtype,
                    trust_remote_code=True,
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
        """Unload current model and free VRAM."""
        del self._model
        del self._processor
        self._model = None
        self._processor = None
        self._current_model_type = None

        # Force garbage collection
        gc.collect()

        # Clear CUDA cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
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

    def get_vram_usage(self) -> float:
        """Get current VRAM usage in GB."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / (1024 ** 3)
        except ImportError:
            pass
        return 0.0

    def unload(self):
        """Explicitly unload the current model."""
        with self._load_lock:
            if self._model is not None:
                self._unload_current()
