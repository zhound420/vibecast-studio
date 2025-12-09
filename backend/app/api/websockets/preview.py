"""WebSocket handler for real-time audio preview streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any
import json
import asyncio

router = APIRouter()


def tensor_to_numpy(tensor: Any) -> Any:
    """
    Safely convert a PyTorch tensor to numpy array.

    Handles CUDA, MPS, and CPU tensors by ensuring they are moved
    to CPU before calling .numpy().
    """
    if hasattr(tensor, "cpu"):
        tensor = tensor.cpu()
    if hasattr(tensor, "detach"):
        tensor = tensor.detach()
    if hasattr(tensor, "numpy"):
        return tensor.numpy()
    return tensor


@router.websocket("/preview")
async def preview_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio preview using VibeVoice-Realtime-0.5B.

    Client sends:
    - {"type": "preview", "text": "...", "voice": "en-Carter_man"}
    - {"type": "stop"}
    - "ping"

    Server sends:
    - Binary audio chunks (raw PCM 24kHz mono)
    - {"type": "start_stream"}
    - {"type": "end_stream"}
    - {"type": "error", "message": "..."}
    - "pong"
    """
    await websocket.accept()

    # Track if we're currently streaming
    is_streaming = False
    should_stop = False

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "model": "VibeVoice-Realtime-0.5B",
        })

        while True:
            # Receive client message
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if "text" in message:
                data = message["text"]

                if data == "ping":
                    await websocket.send_text("pong")
                    continue

                try:
                    request = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON",
                    })
                    continue

                if request.get("type") == "stop":
                    should_stop = True
                    continue

                if request.get("type") == "preview":
                    text = request.get("text", "")
                    voice = request.get("voice", "en-Carter_man")

                    if not text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No text provided",
                        })
                        continue

                    # Start streaming
                    is_streaming = True
                    should_stop = False

                    await websocket.send_json({"type": "start_stream"})

                    try:
                        # Generate audio preview
                        await _generate_preview_stream(
                            websocket, text, voice, lambda: should_stop
                        )
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                        })

                    await websocket.send_json({"type": "end_stream"})
                    is_streaming = False

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


async def _generate_preview_stream(
    websocket: WebSocket,
    text: str,
    voice: str,
    should_stop_fn,
):
    """
    Generate audio preview using the Realtime model and stream to client.

    In production, this would:
    1. Load the VibeVoice-Realtime-0.5B model
    2. Generate audio in streaming mode
    3. Send audio chunks as binary WebSocket messages
    """
    from app.services.vibevoice.model_manager import ModelManager

    try:
        # Get the model manager
        model_manager = ModelManager()

        # Check if we should use a mock for development
        # In production, this would load the actual model
        use_mock = True  # Set to False when model is available

        if use_mock:
            # Send mock audio data for testing
            # This simulates streaming audio chunks
            import numpy as np

            sample_rate = 24000
            duration_per_chunk = 0.1  # 100ms chunks
            samples_per_chunk = int(sample_rate * duration_per_chunk)

            # Generate simple sine wave for testing
            total_duration = min(len(text) / 15, 10)  # ~15 chars/sec, max 10s
            total_chunks = int(total_duration / duration_per_chunk)

            for i in range(total_chunks):
                if should_stop_fn():
                    break

                # Generate a chunk of audio (simple tone for mock)
                t = np.linspace(
                    i * duration_per_chunk,
                    (i + 1) * duration_per_chunk,
                    samples_per_chunk,
                )
                # 440 Hz sine wave
                audio_chunk = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)

                # Send as binary
                await websocket.send_bytes(audio_chunk.tobytes())

                # Small delay to simulate real generation
                await asyncio.sleep(0.05)

        else:
            # Real model generation
            model, processor = model_manager.load_model("realtime")

            # Process input
            inputs = processor(
                text,
                speaker_name=voice,
                return_tensors="pt",
            ).to(model.device)

            # Generate with streaming (if supported)
            # This is model-specific implementation
            for audio_chunk in model.generate_streaming(**inputs):
                if should_stop_fn():
                    break

                # Safely convert tensor to numpy (handles CUDA/MPS/CPU)
                audio_np = tensor_to_numpy(audio_chunk)
                audio_bytes = audio_np.astype("float32").tobytes()
                await websocket.send_bytes(audio_bytes)

    except Exception as e:
        raise Exception(f"Preview generation failed: {str(e)}")
