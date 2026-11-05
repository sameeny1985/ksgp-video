"""Fetch YouTube title/thumbnail via oEmbed (no API key required)."""
import re
import json
import urllib.parse
import urllib.request


YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})'
)


def extract_youtube_id(url: str) -> str:
    if not url:
        return ''
    m = YOUTUBE_ID_RE.search(url)
    return m.group(1) if m else ''


def fetch_youtube_meta(url: str, timeout: float = 6.0) -> dict:
    """
    Returns dict: video_id, title, thumbnail_url, author_name, html (optional)
    Uses YouTube oEmbed endpoint.
    """
    video_id = extract_youtube_id(url)
    result = {
        'video_id': video_id,
        'title': '',
        'thumbnail_url': '',
        'author_name': '',
    }
    if not video_id:
        return result

    # Default thumbnail even if oEmbed fails
    result['thumbnail_url'] = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'

    oembed = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote(
        f'https://www.youtube.com/watch?v={video_id}', safe=''
    )
    try:
        req = urllib.request.Request(
            oembed,
            headers={'User-Agent': 'KSGP-Video/1.0'},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
        result['title'] = (data.get('title') or '')[:200]
        if data.get('thumbnail_url'):
            result['thumbnail_url'] = data['thumbnail_url']
        result['author_name'] = data.get('author_name') or ''
    except Exception:
        # keep thumbnail default; title stays empty if oEmbed blocked
        pass
    return result
