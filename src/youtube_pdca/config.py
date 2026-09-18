from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ChannelConfig:
    url: str | None = None
    channel_id: str | None = None
    name: str | None = None

    def identifier(self) -> str:
        value = self.channel_id or self.url or self.name
        if not value:
            raise ValueError("チャンネル設定に url / channel_id / name のいずれかを指定してください")
        return value


@dataclass
class AppConfig:
    own_channel: ChannelConfig
    competitor_channels: list[ChannelConfig]
    max_videos_per_channel: int = 30
    top_n_for_pattern: int = 10


def load_config(path: Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    own_raw = raw["own_channel"]
    own_channel = ChannelConfig(
        url=own_raw.get("url"),
        channel_id=own_raw.get("channel_id"),
        name=own_raw.get("name"),
    )

    competitors = [
        ChannelConfig(url=c.get("url"), channel_id=c.get("channel_id"), name=c.get("name"))
        for c in raw.get("competitor_channels", [])
    ]

    analysis = raw.get("analysis", {})

    return AppConfig(
        own_channel=own_channel,
        competitor_channels=competitors,
        max_videos_per_channel=analysis.get("max_videos_per_channel", 30),
        top_n_for_pattern=analysis.get("top_n_for_pattern", 10),
    )
