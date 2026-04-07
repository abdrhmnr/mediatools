"""Video & Audio Tools using FFmpeg"""
import os
import subprocess
import shutil


def _ffmpeg(args, timeout=600):
    cmd = ['ffmpeg', '-y'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-1000:]}")
    return result


QUALITY_PRESETS = {
    'low':    {'crf': '35', 'preset': 'veryfast'},
    'medium': {'crf': '28', 'preset': 'fast'},
    'high':   {'crf': '20', 'preset': 'medium'},
    'best':   {'crf': '15', 'preset': 'slow'},
}


def convert_video(input_path, output_path, fmt, quality='medium'):
    q = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['medium'])
    args = ['-i', input_path]
    if fmt in ('mp4', 'mkv', 'avi', 'mov', 'webm'):
        if fmt == 'webm':
            args += ['-c:v', 'libvpx-vp9', '-crf', q['crf'], '-b:v', '0', '-c:a', 'libopus']
        else:
            args += ['-c:v', 'libx264', '-crf', q['crf'], '-preset', q['preset'], '-c:a', 'aac']
    args.append(output_path)
    _ffmpeg(args)
    return {'file': os.path.basename(output_path), 'path': output_path}


def extract_audio(input_path, output_path, fmt='mp3'):
    codec_map = {'mp3': 'libmp3lame', 'aac': 'aac', 'ogg': 'libvorbis',
                 'flac': 'flac', 'wav': 'pcm_s16le', 'm4a': 'aac', 'opus': 'libopus'}
    codec = codec_map.get(fmt, 'libmp3lame')
    args = ['-i', input_path, '-vn', '-c:a', codec, '-q:a', '2', output_path]
    _ffmpeg(args)
    return {'file': os.path.basename(output_path), 'path': output_path}


def trim_video(input_path, output_path, start, end):
    args = ['-i', input_path, '-ss', str(start), '-to', str(end),
            '-c:v', 'libx264', '-c:a', 'aac', '-avoid_negative_ts', 'make_zero', output_path]
    _ffmpeg(args)
    return {'file': os.path.basename(output_path), 'path': output_path}


def compress_video(input_path, output_path, quality='medium'):
    q = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['medium'])
    original = os.path.getsize(input_path)
    args = ['-i', input_path, '-c:v', 'libx264', '-crf', q['crf'],
            '-preset', q['preset'], '-c:a', 'aac', '-b:a', '128k', output_path]
    _ffmpeg(args)
    compressed = os.path.getsize(output_path)
    ratio = round((1 - compressed / original) * 100, 1) if original > 0 else 0
    return {
        'file': os.path.basename(output_path),
        'path': output_path,
        'original_size': original,
        'compressed_size': compressed,
        'reduction': f"{ratio}%"
    }


def convert_audio(input_path, output_path, fmt='mp3'):
    codec_map = {'mp3': 'libmp3lame', 'aac': 'aac', 'ogg': 'libvorbis',
                 'flac': 'flac', 'wav': 'pcm_s16le', 'm4a': 'aac', 'opus': 'libopus'}
    codec = codec_map.get(fmt, 'libmp3lame')
    args = ['-i', input_path, '-c:a', codec, '-q:a', '2', output_path]
    _ffmpeg(args)
    return {'file': os.path.basename(output_path), 'path': output_path}
