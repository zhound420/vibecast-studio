"""Content segmenter for intelligent speaker assignment."""

import re
from typing import List, Dict


class ContentSegmenter:
    """
    Intelligent content segmenter that splits text and assigns speakers.

    Strategies:
    - paragraph: Split on double newlines, alternate speakers
    - sentence: Split on sentence boundaries, alternate speakers
    - auto: Use NLP-like heuristics for smart assignment
    """

    def segment(
        self,
        content: str,
        num_speakers: int = 2,
        style: str = "auto",
    ) -> List[Dict]:
        """
        Segment content and assign speakers.

        Args:
            content: Text content to segment
            num_speakers: Number of speakers to use (1-4)
            style: Segmentation style (auto, paragraph, sentence)

        Returns:
            List of segment dictionaries
        """
        num_speakers = min(max(num_speakers, 1), 4)

        if style == "paragraph":
            return self._segment_by_paragraph(content, num_speakers)
        elif style == "sentence":
            return self._segment_by_sentence(content, num_speakers)
        else:
            return self._segment_auto(content, num_speakers)

    def _segment_by_paragraph(
        self,
        content: str,
        num_speakers: int,
    ) -> List[Dict]:
        """Split by paragraphs, alternating speakers."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        segments = []
        for i, para in enumerate(paragraphs):
            speaker_id = (i % num_speakers) + 1
            segments.append({
                "text": para,
                "speaker_id": speaker_id,
                "speaker_name": f"Speaker {speaker_id}",
            })

        return segments

    def _segment_by_sentence(
        self,
        content: str,
        num_speakers: int,
    ) -> List[Dict]:
        """Split by sentences, alternating speakers."""
        # Simple sentence splitting (could use NLTK for better results)
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())

        segments = []
        current_speaker = 1
        current_text = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            current_text.append(sentence)

            # Group 2-3 sentences per segment
            if len(current_text) >= 2 or sentence.endswith("?"):
                segments.append({
                    "text": " ".join(current_text),
                    "speaker_id": current_speaker,
                    "speaker_name": f"Speaker {current_speaker}",
                })
                current_text = []
                current_speaker = (current_speaker % num_speakers) + 1

        # Add remaining text
        if current_text:
            segments.append({
                "text": " ".join(current_text),
                "speaker_id": current_speaker,
                "speaker_name": f"Speaker {current_speaker}",
            })

        return segments

    def _segment_auto(
        self,
        content: str,
        num_speakers: int,
    ) -> List[Dict]:
        """
        Intelligent segmentation using heuristics.

        Rules:
        - Questions are followed by responses from different speaker
        - Bullet points/lists stay with same speaker
        - Topic changes (headers) can trigger speaker change
        - Long paragraphs may be split
        """
        lines = content.split("\n")
        segments = []
        current_speaker = 1
        current_text = []
        last_was_question = False

        for line in lines:
            line = line.strip()
            if not line:
                # Paragraph break
                if current_text:
                    segments.append({
                        "text": " ".join(current_text),
                        "speaker_id": current_speaker,
                        "speaker_name": f"Speaker {current_speaker}",
                    })
                    current_text = []

                    # Switch speaker on paragraph break (for 2-speaker mode)
                    if num_speakers == 2:
                        current_speaker = 3 - current_speaker
                    else:
                        current_speaker = (current_speaker % num_speakers) + 1
                continue

            # Check for headers (could indicate topic change)
            if line.startswith("#") or (line.isupper() and len(line) < 100):
                if current_text:
                    segments.append({
                        "text": " ".join(current_text),
                        "speaker_id": current_speaker,
                        "speaker_name": f"Speaker {current_speaker}",
                    })
                    current_text = []

                # Headers go to speaker 1
                current_speaker = 1

            # Check for questions
            if line.endswith("?"):
                current_text.append(line)
                segments.append({
                    "text": " ".join(current_text),
                    "speaker_id": current_speaker,
                    "speaker_name": f"Speaker {current_speaker}",
                })
                current_text = []
                # Response should be from different speaker
                current_speaker = (current_speaker % num_speakers) + 1
                last_was_question = True
                continue

            # Check for bullet points
            if line.startswith(("-", "*", "•", "·")):
                # Keep bullet points with current speaker
                current_text.append(line.lstrip("-*•· "))
                continue

            current_text.append(line)
            last_was_question = False

        # Add remaining text
        if current_text:
            segments.append({
                "text": " ".join(current_text),
                "speaker_id": current_speaker,
                "speaker_name": f"Speaker {current_speaker}",
            })

        return segments
