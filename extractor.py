import json
import re
from typing import Tuple, Optional
import httpx

# Using a modern Windows Chrome user agent to get past initial cloudflare/akamai filters
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def resolve_url(url: str) -> str:
    if "tiktok.com" not in url:
        raise ValueError("Not a valid TikTok URL")
    
    # Follow redirects cleanly to get the canonical browser URL
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to resolve URL, status code {resp.status_code}")
        return str(resp.url)

def extract_video_id(url: str) -> str:
    # Handles both standard desktop /video/123456 and mobile /v/123456 structures
    match = re.search(r"/(?:video|v)/(\d+)", url)
    if not match:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    return match.group(1)

def _extract_from_html(html: str) -> Optional[str]:
    # Attempt HTML decoding from typical modern client-state scripts
    for pattern in [
        r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
        r'<script id="SIGI_STATE" type="application/json">(.*?)</script>'
    ]:
        match = re.search(pattern, html)
        if match:
            try:
                data = json.loads(match.group(1))
                # print(json.dumps(data, indent=2)) # left in for raw debugging if struct changes again
                
                default_scope = data.get("__DEFAULT_SCOPE__", {})
                detail = default_scope.get("webapp.video-detail", {})
                if detail:
                    item_info = detail.get("itemInfo", {})
                else:
                    item_info = data.get("itemInfo", {})
                    
                item_struct = item_info.get("itemStruct", {})
                if item_struct:
                    video_info = item_struct.get("video", {})
                    return video_info.get("playAddr") or video_info.get("downloadAddr")
            except (json.JSONDecodeError, KeyError, AttributeError):
                continue
    return None

def _fetch_fallback_api(video_url: str) -> Optional[str]:
    # Fallback to tikwm API since browser-emulation scraping of TikTok is highly fragile
    # and gets rate-limited or JS-challenged almost instantly under load.
    api_url = "https://www.tikwm.com/api/"
    try:
        with httpx.Client(headers=HEADERS, timeout=10.0) as client:
            resp = client.post(api_url, data={"url": video_url})
            if resp.status_code == 200:
                res_json = resp.json()
                data = res_json.get("data", {})
                # 'play' points to the clean, watermark-free direct mp4 stream
                return data.get("play") or data.get("wmplay")
    except Exception:
        # Let the caller bubble up or try next options; don't dump raw traceback here
        pass
    return None

def get_video_stream_url(url: str) -> Tuple[str, str]:
    """
    Resolves the final video stream URL and returns a tuple:
    (stream_url, video_id)
    """
    resolved = resolve_url(url)
    video_id = extract_video_id(resolved)
    
    # 1. Try local html scraping first to bypass third-party api dependency
    try:
        with httpx.Client(headers=HEADERS, timeout=10.0) as client:
            resp = client.get(resolved)
            if resp.status_code == 200:
                stream_url = _extract_from_html(resp.text)
                if stream_url:
                    return stream_url, video_id
    except Exception:
        pass

    # FIXME: TikTok's scraper challenge blocks are extremely dynamic.
    # Fall back immediately to our API helper if html scrape returns empty or fails.
    stream_url = _fetch_fallback_api(resolved)
    if not stream_url:
        raise RuntimeError("Could not extract unwatermarked video stream using either direct scraping or fallback API.")
        
    return stream_url, video_id
