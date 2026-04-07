"""Downloader: generic URL, YouTube, social media via yt-dlp"""
import os
import uuid
import requests
import subprocess
from urllib.parse import urlparse


def _run_ytdlp(args, timeout=900):
    cmd = ['yt-dlp'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp error: {result.stderr[-2000:]}")
    return result.stdout


def download_file(url, output_dir):
    """Download any file from a direct URL"""
    parsed = urlparse(url)
    fname = os.path.basename(parsed.path) or f"download_{uuid.uuid4()}"
    # sanitize
    fname = "".join(c for c in fname if c.isalnum() or c in '._-')
    if not fname or fname == '':
        fname = f"download_{uuid.uuid4()}"
    # prefix uid to avoid collision
    uid = str(uuid.uuid4())[:8]
    fname = f"{uid}_{fname}"
    output_path = os.path.join(output_dir, fname)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    with requests.get(url, stream=True, headers=headers, timeout=60) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return {'file': fname, 'path': output_path}


def download_youtube(url, output_dir, fmt='video', quality='best'):
    """Download YouTube video or audio, supports playlists"""
    uid = str(uuid.uuid4())[:8]
    template = os.path.join(output_dir, f"{uid}_%(title).50s.%(ext)s")

    if fmt == 'audio':
        args = [
            url,
            '-x', '--audio-format', 'mp3',
            '--audio-quality', '0',
            '-o', template,
            '--no-playlist' if '?v=' in url else '--yes-playlist',
        ]
    else:
        q_format = {
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
            '360p': 'worst[ext=mp4]/worst',
        }.get(quality, 'best[ext=mp4]/best')
        args = [
            url, '-f', q_format,
            '--merge-output-format', 'mp4',
            '-o', template,
            '--no-playlist' if '?v=' in url and 'list' not in url else '--yes-playlist',
        ]

    # Add metadata and thumbnail embedding
    args += ['--add-metadata', '--embed-thumbnail', '--convert-thumbnails', 'jpg']

    stdout = _run_ytdlp(args)

    # Find downloaded files
    files = []
    for line in stdout.split('\n'):
        if '[download] Destination:' in line or 'Merging formats into' in line:
            path = line.split(':', 1)[-1].strip().strip('"')
            if os.path.exists(path):
                files.append({'file': os.path.basename(path), 'path': path})

    if not files:
        # fallback: find newest files in output dir matching our uid
        import glob, time
        pattern = os.path.join(output_dir, f"{uid}_*")
        found = glob.glob(pattern)
        files = [{'file': os.path.basename(p), 'path': p} for p in found]

    return {'files': files, 'count': len(files)}


def download_social(url, output_dir):
    """Download from social media (Instagram, Twitter/X, TikTok, Facebook, etc.)"""
    uid = str(uuid.uuid4())[:8]
    template = os.path.join(output_dir, f"{uid}_%(title).50s.%(ext)s")
    args = [
        url,
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '-o', template,
        '--add-metadata',
    ]
    stdout = _run_ytdlp(args)

    import glob
    pattern = os.path.join(output_dir, f"{uid}_*")
    found = glob.glob(pattern)
    files = [{'file': os.path.basename(p), 'path': p} for p in found]
    return {'files': files, 'count': len(files)}
