"""
语音播报服务 - 基于 Edge TTS 的红色故事朗读
"""
import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional

import config


class TTSService:
    """Edge TTS 语音合成"""

    VOICES = {
        "zh-CN-XiaoxiaoNeural": "晓晓（女声，温柔）",
        "zh-CN-YunxiNeural": "云希（男声，叙事）",
        "zh-CN-YunjianNeural": "云健（男声，沉稳）",
        "zh-CN-XiaoyiNeural": "晓伊（女声，知性）",
    }

    def __init__(self, voice: str = "zh-CN-YunxiNeural"):
        self.voice = voice
        self.audio_dir = config.ROOT_DIR / "media" / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def _synthesize(self, text: str, output_path: str) -> bool:
        """调用 edge-tts 合成语音"""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            print(f"[TTS Error] {e}")
            return False

    def synthesize(self, text: str, title: str = "") -> Optional[dict]:
        """同步合成语音"""
        file_id = uuid.uuid4().hex[:12]
        filename = f"{file_id}.mp3"
        output_path = self.audio_dir / filename

        success = asyncio.run(self._synthesize(text, str(output_path)))
        if not success:
            return None

        from .media_manager import MediaManager
        mm = MediaManager()
        entry = mm.add(
            str(output_path),
            title=title or "红色故事播报",
            tags=["tts", "narration"],
        )
        return entry

    def narrate_story(self, story_text: str, title: str = "红色故事") -> Optional[dict]:
        """朗读红色故事"""
        return self.synthesize(story_text, title)

    def list_voices(self) -> dict:
        """列出可用语音"""
        return self.VOICES