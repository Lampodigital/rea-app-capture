#!/usr/bin/env python3
"""Estrai e decodifica fotogrammi PNG da un video locale; richiede ffmpeg e Pillow."""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import warnings


def ffmpeg_path(explicit):
    if explicit:
        return explicit
    found = shutil.which('ffmpeg')
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise ValueError('ffmpeg not found; supply --ffmpeg or use an existing installation')


def png_dimensions(path):
    from PIL import Image
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as picture:
            if picture.format != 'PNG':
                raise ValueError('Output is not PNG')
            picture.verify()
        with Image.open(path) as picture:
            picture.load()
            if picture.width <= 0 or picture.height <= 0:
                raise ValueError('PNG has no decoded image')
            return picture.size


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video', type=Path)
    p.add_argument('--output', type=Path, required=True, help='New directory; existing directories are refused')
    p.add_argument('--times', required=True, help='Comma-separated seconds relative to this local file')
    p.add_argument('--ffmpeg')
    p.add_argument('--source-url')
    p.add_argument('--source-start', type=float, help='Declared approximate offset in original video')
    args = p.parse_args()
    times = [float(s.strip()) for s in args.times.split(',')]
    if not times or len(times) > 100 or any(not math.isfinite(t) or t < 0 for t in times):
        raise ValueError('Supply 1–100 finite nonnegative timestamps')
    if args.source_start is not None and (not math.isfinite(args.source_start) or args.source_start < 0):
        raise ValueError('Invalid source offset')
    video = args.video.resolve(strict=True)
    if not video.is_file():
        raise ValueError('Expected local video file')
    try:
        from PIL import Image
    except ImportError:
        raise ValueError('Pillow required to decode frames; install the documented video dependencies')
    ffmpeg = ffmpeg_path(args.ffmpeg)
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {'source_file': video.name, 'source_sha256': None, 'source_url': args.source_url,
              'source_start_declared': args.source_start, 'source_time_precision': 'approximate if offset supplied',
              'created_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'frames': []}
    h = hashlib.sha256()
    with video.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    report['source_sha256'] = h.hexdigest()
    for index, timestamp in enumerate(times):
        output = args.output / f'frame-{index + 1:03d}.png'
        item = {'file': output.name, 'local_seconds': timestamp, 'status': 'failed'}
        if args.source_start is not None:
            item['approximate_source_seconds'] = args.source_start + timestamp
        try:
            result = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-n',
                                     '-protocol_whitelist', 'file,pipe', '-i', str(video), '-ss', str(timestamp), '-map', '0:v:0',
                                     '-frames:v', '1', '-an', str(output)], capture_output=True, timeout=60)
            if result.returncode:
                raise ValueError('ffmpeg failed: ' + result.stderr.decode(errors='replace')[-500:])
            width, height = png_dimensions(output)
            item.update(status='decoded', width=width, height=height,
                        sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombWarning,
                Image.DecompressionBombError, subprocess.TimeoutExpired) as exc:
            item['error'] = str(exc)
            if output.exists():
                output.unlink()
        report['frames'].append(item)
    report['complete'] = all(f['status'] == 'decoded' for f in report['frames'])
    (args.output / 'frames.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'complete': report['complete'], 'decoded': sum(f['status'] == 'decoded' for f in report['frames']),
                      'requested': len(times), 'report': str(args.output / 'frames.json')}))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(2)
