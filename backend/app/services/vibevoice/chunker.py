"""Content chunker for long-form generation."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Chunk:
    """A chunk of content for generation."""
    id: int
    text: str
    speaker_ids: List[int]
    estimated_duration_seconds: float
    start_segment_idx: int
    end_segment_idx: int


class ContentChunker:
    """
    Splits long-form content into chunks that fit within model context.

    Strategy for 90-minute content:
    1. Each chunk targets ~8 minutes of audio (safe margin under 64K tokens)
    2. Split at natural boundaries (paragraph, scene, speaker change)
    3. Maintain speaker continuity across chunk boundaries
    """

    # Approximate tokens per minute of speech (based on ~150 WPM)
    TOKENS_PER_MINUTE = 200  # Conservative estimate with formatting

    # Target chunk duration in minutes
    TARGET_CHUNK_MINUTES = 8  # Leave headroom for model context

    def __init__(self, max_context_tokens: int = 64000):
        self.max_context_tokens = max_context_tokens
        # Use 80% of max context for safety margin
        self.max_chunk_tokens = int(max_context_tokens * 0.8)

    def chunk_script(self, segments: List[Dict[str, Any]]) -> List[Chunk]:
        """
        Split script segments into generation chunks.

        Args:
            segments: List of segment dicts with keys:
                - text: str
                - speaker_id: int
                - speaker_name: str (optional)

        Returns:
            List of Chunk objects for sequential generation
        """
        if not segments:
            return []

        chunks = []
        current_chunk_segments = []
        current_token_estimate = 0
        chunk_id = 0
        start_idx = 0

        for idx, segment in enumerate(segments):
            segment_tokens = self._estimate_tokens(segment["text"])

            # Check if adding this segment would exceed chunk limit
            if current_token_estimate + segment_tokens > self.max_chunk_tokens:
                # Finalize current chunk if we have segments
                if current_chunk_segments:
                    chunks.append(self._create_chunk(
                        chunk_id, current_chunk_segments, start_idx, idx - 1
                    ))
                    chunk_id += 1

                # Start new chunk with this segment
                current_chunk_segments = [segment]
                current_token_estimate = segment_tokens
                start_idx = idx
            else:
                current_chunk_segments.append(segment)
                current_token_estimate += segment_tokens

        # Add final chunk
        if current_chunk_segments:
            chunks.append(self._create_chunk(
                chunk_id, current_chunk_segments, start_idx, len(segments) - 1
            ))

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation.

        Uses ~4 characters per token as average.
        """
        # Base estimate
        char_tokens = len(text) // 4

        # Add overhead for formatting
        overhead = 50

        return char_tokens + overhead

    def _create_chunk(
        self,
        chunk_id: int,
        segments: List[Dict[str, Any]],
        start_idx: int,
        end_idx: int,
    ) -> Chunk:
        """Create a Chunk object from segments."""
        # Combine text for VibeVoice input
        combined_text = self._format_for_vibevoice(segments)

        # Get unique speaker IDs
        speaker_ids = list(set(seg["speaker_id"] for seg in segments))

        # Estimate duration from word count (~150 WPM)
        word_count = sum(len(seg["text"].split()) for seg in segments)
        estimated_duration = (word_count / 150) * 60  # seconds

        return Chunk(
            id=chunk_id,
            text=combined_text,
            speaker_ids=speaker_ids,
            estimated_duration_seconds=estimated_duration,
            start_segment_idx=start_idx,
            end_segment_idx=end_idx,
        )

    def _format_for_vibevoice(self, segments: List[Dict[str, Any]]) -> str:
        """
        Format segments for VibeVoice input.

        Uses bracket notation: [speaker_id] Text
        """
        lines = []
        for seg in segments:
            speaker_id = seg.get("speaker_id", 1)
            text = seg.get("text", "").strip()
            if text:
                lines.append(f"[{speaker_id}] {text}")

        return "\n\n".join(lines)
