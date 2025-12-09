"""Audio stitcher for combining chunk files."""

from pathlib import Path
from typing import List
import asyncio
import subprocess


class AudioStitcher:
    """
    Stitches multiple audio chunks into a single file.

    Uses FFmpeg for crossfade concatenation.
    """

    def __init__(self, crossfade_ms: int = 500):
        """
        Initialize stitcher.

        Args:
            crossfade_ms: Crossfade duration in milliseconds
        """
        self.crossfade_ms = crossfade_ms
        self.crossfade_seconds = crossfade_ms / 1000

    async def stitch(self, chunk_files: List[Path], output_path: Path) -> Path:
        """
        Stitch multiple audio files into one.

        Args:
            chunk_files: List of paths to chunk audio files
            output_path: Path for the output file

        Returns:
            Path to the stitched output file
        """
        if not chunk_files:
            raise ValueError("No chunk files provided")

        if len(chunk_files) == 1:
            # Single file, just copy it
            await self._copy_file(chunk_files[0], output_path)
            return output_path

        # Build FFmpeg filter for crossfade concatenation
        filter_complex = self._build_crossfade_filter(len(chunk_files))

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Add input files
        for chunk_file in chunk_files:
            cmd.extend(["-i", str(chunk_file)])

        # Add filter complex
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", f"[out]",
            str(output_path),
        ])

        # Run FFmpeg
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._run_ffmpeg(cmd))

        return output_path

    def _build_crossfade_filter(self, num_files: int) -> str:
        """
        Build FFmpeg filter_complex string for crossfade concatenation.

        Example for 3 files:
        [0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a01];[a01][2:a]acrossfade=d=0.5:c1=tri:c2=tri[out]
        """
        if num_files < 2:
            return "[0:a]acopy[out]"

        filters = []
        prev_output = "0:a"

        for i in range(1, num_files):
            if i == num_files - 1:
                output_label = "out"
            else:
                output_label = f"a{i}"

            filters.append(
                f"[{prev_output}][{i}:a]acrossfade=d={self.crossfade_seconds}:"
                f"c1=tri:c2=tri[{output_label}]"
            )
            prev_output = output_label

        return ";".join(filters)

    def _run_ffmpeg(self, cmd: List[str]):
        """Run FFmpeg command."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg timed out")

    async def _copy_file(self, src: Path, dst: Path):
        """Copy a file asynchronously."""
        import shutil

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: shutil.copy2(src, dst))


class SimpleStitcher:
    """
    Simple stitcher that concatenates without crossfade.

    Useful as a fallback if FFmpeg is not available.
    """

    async def stitch(self, chunk_files: List[Path], output_path: Path) -> Path:
        """Concatenate audio files without crossfade."""
        import numpy as np
        import scipy.io.wavfile as wavfile

        if not chunk_files:
            raise ValueError("No chunk files provided")

        # Read all chunks
        audio_data = []
        sample_rate = None

        for chunk_file in chunk_files:
            sr, data = wavfile.read(str(chunk_file))
            if sample_rate is None:
                sample_rate = sr
            elif sr != sample_rate:
                raise ValueError(f"Sample rate mismatch: {sr} vs {sample_rate}")
            audio_data.append(data)

        # Concatenate
        combined = np.concatenate(audio_data)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wavfile.write(str(output_path), sample_rate, combined)

        return output_path
