"""
多媒体资源管理 - 图片、视频、音频的存储与检索
"""
import os
import json
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import config


class MediaManager:
    """统一管理图片、视频、音频资源"""

    ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    ALLOWED_VIDEO = {".mp4", ".webm", ".avi", ".mov"}
    ALLOWED_AUDIO = {".mp3", ".wav", ".ogg", ".m4a"}

    def __init__(self):
        self.media_dir = config.ROOT_DIR / "media"
        self.images_dir = self.media_dir / "images"
        self.videos_dir = self.media_dir / "videos"
        self.audio_dir = self.media_dir / "audio"
        self.meta_file = self.media_dir / "metadata.json"

        for d in [self.images_dir, self.videos_dir, self.audio_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self._meta = None

    @property
    def metadata(self) -> dict:
        if self._meta is None:
            if self.meta_file.exists():
                self._meta = json.loads(self.meta_file.read_text(encoding="utf-8"))
            else:
                self._meta = {"images": {}, "videos": {}, "audio": {}}
        return self._meta

    def _save_meta(self):
        self.meta_file.write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _classify(self, ext: str) -> str:
        ext = ext.lower()
        if ext in self.ALLOWED_IMAGE: return "images"
        if ext in self.ALLOWED_VIDEO: return "videos"
        if ext in self.ALLOWED_AUDIO: return "audio"
        return None

    def add(self, file_path: str, title: str = "", tags: List[str] = None) -> dict:
        """添加媒体资源"""
        src = Path(file_path)
        ext = src.suffix.lower()
        media_type = self._classify(ext)
        if not media_type:
            raise ValueError(f"不支持的媒体格式: {ext}")

        file_id = uuid.uuid4().hex[:12]
        new_name = f"{file_id}{ext}"
        dest_dir = self.media_dir / media_type
        dest = dest_dir / new_name
        shutil.copy2(src, dest)

        entry = {
            "id": file_id,
            "filename": new_name,
            "original_name": src.name,
            "title": title or src.stem,
            "tags": tags or [],
            "type": media_type,
            "path": f"media/{media_type}/{new_name}",
            "size": os.path.getsize(dest),
            "upload_time": datetime.now().isoformat(),
        }
        self.metadata[media_type][file_id] = entry
        self._save_meta()
        return entry

    def list(self, media_type: str = None, tag: str = None) -> List[dict]:
        """列出媒体资源"""
        result = []
        types = [media_type] if media_type else ["images", "videos", "audio"]
        for t in types:
            for entry in self.metadata.get(t, {}).values():
                if tag and tag not in entry.get("tags", []):
                    continue
                result.append(entry)
        return sorted(result, key=lambda x: x.get("upload_time", ""), reverse=True)

    def get(self, file_id: str) -> Optional[dict]:
        """获取单个资源信息"""
        for t in ["images", "videos", "audio"]:
            if file_id in self.metadata.get(t, {}):
                return self.metadata[t][file_id]
        return None

    def delete(self, file_id: str) -> bool:
        """删除媒体资源"""
        entry = self.get(file_id)
        if not entry:
            return False

        file_path = config.ROOT_DIR / entry["path"]
        if file_path.exists():
            file_path.unlink()

        del self.metadata[entry["type"]][file_id]
        self._save_meta()
        return True

    def update(self, file_id: str, title: str = None, tags: List[str] = None) -> bool:
        """更新资源元信息"""
        entry = self.get(file_id)
        if not entry:
            return False
        if title:
            entry["title"] = title
        if tags is not None:
            entry["tags"] = tags
        self._save_meta()
        return True

    def search_related(self, keywords: List[str], limit: int = 5) -> List[dict]:
        """根据关键词搜索相关媒体"""
        all_media = self.list()
        scored = []
        for m in all_media:
            score = 0
            text = m.get("title", "") + " " + " ".join(m.get("tags", []))
            for kw in keywords:
                if kw in text:
                    score += 1
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]