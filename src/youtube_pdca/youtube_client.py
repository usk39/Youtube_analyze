from __future__ import annotations

import re

CHANNEL_ID_RE = re.compile(r"^UC[0-9A-Za-z_-]{22}$")


def resolve_channel_id(youtube, url_or_id: str) -> str:
    """URL・ハンドル(@xxx)・チャンネルIDのいずれを渡してもチャンネルIDに解決する。"""
    value = url_or_id.strip()

    if CHANNEL_ID_RE.match(value):
        return value

    handle = None
    custom_name = None
    channel_id_from_url = None

    m = re.search(r"youtube\.com/channel/([0-9A-Za-z_-]+)", value)
    if m:
        channel_id_from_url = m.group(1)
    else:
        m = re.search(r"youtube\.com/@([^/?&]+)", value)
        if m:
            handle = m.group(1)
        else:
            m = re.search(r"youtube\.com/(?:c|user)/([^/?&]+)", value)
            if m:
                custom_name = m.group(1)
            elif value.startswith("@"):
                handle = value[1:]
            else:
                custom_name = value

    if channel_id_from_url:
        return channel_id_from_url

    if handle:
        resp = youtube.channels().list(part="id", forHandle=handle).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["id"]

    if custom_name:
        try:
            resp = youtube.channels().list(part="id", forUsername=custom_name).execute()
            items = resp.get("items", [])
            if items:
                return items[0]["id"]
        except Exception:
            pass

    query = handle or custom_name or value
    resp = youtube.search().list(part="snippet", q=query, type="channel", maxResults=1).execute()
    items = resp.get("items", [])
    if items:
        return items[0]["snippet"]["channelId"]

    raise ValueError(f"チャンネルIDを特定できませんでした: {url_or_id}")


def get_channel_stats(youtube, channel_id: str) -> dict:
    resp = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"チャンネル情報が取得できませんでした: {channel_id}")

    item = items[0]
    stats = item.get("statistics", {})
    return {
        "channel_id": channel_id,
        "title": item["snippet"]["title"],
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def get_recent_video_ids(youtube, uploads_playlist_id: str, max_results: int) -> list[str]:
    video_ids: list[str] = []
    page_token = None

    while len(video_ids) < max_results:
        resp = (
            youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=page_token,
            )
            .execute()
        )
        for item in resp.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def get_videos_details(youtube, video_ids: list[str]) -> list[dict]:
    videos: list[dict] = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        resp = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(chunk)).execute()
        videos.extend(resp.get("items", []))
    return videos


def get_recent_videos(youtube, uploads_playlist_id: str, max_results: int) -> list[dict]:
    video_ids = get_recent_video_ids(youtube, uploads_playlist_id, max_results)
    return get_videos_details(youtube, video_ids)


def get_top_comments(youtube, video_id: str, max_results: int = 20) -> list[str]:
    """動画の上位コメント本文を取得する。コメント無効化・非公開等で失敗した場合は空リストを返す。"""
    try:
        resp = (
            youtube.commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                maxResults=min(max_results, 100),
                order="relevance",
                textFormat="plainText",
            )
            .execute()
        )
    except Exception:
        return []

    comments = []
    for item in resp.get("items", []):
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        text = snippet.get("textDisplay")
        if text:
            comments.append(text)
    return comments
