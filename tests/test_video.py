"""Video e immagini generati al momento, senza materiale di app reali."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

import imageio_ffmpeg
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/extract_video_frames.py'
spec = importlib.util.spec_from_file_location('extract_video_frames', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / 'video with spaces.mp4'
        subprocess.run([FFMPEG, '-nostdin', '-loglevel', 'error', '-f', 'lavfi', '-i',
                        'color=c=red:s=64x48:d=2:r=10', '-an', str(self.video)], check=True, timeout=20)

    def run_cli(self, *args, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.video), *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result.stdout.strip()

    def test_frames_are_decoded_and_have_expected_pixels(self):
        out = self.root / 'frames'
        result = json.loads(self.run_cli('--output', out, '--times', '0,0.5,1.5',
                                        '--source-url', 'https://example.com/demo', '--source-start', '10', '--ffmpeg', FFMPEG))
        self.assertEqual(result['decoded'], 3)
        self.assertTrue(result['complete'])
        report = json.loads((out / 'frames.json').read_text())
        self.assertEqual(report['frames'][1]['approximate_source_seconds'], 10.5)
        self.assertEqual(report['source_url'], 'https://example.com/demo')
        for entry in report['frames']:
            with Image.open(out / entry['file']) as image:
                image.load()
                self.assertEqual(image.size, (64, 48))
                red, green, blue = image.convert('RGB').getpixel((32, 24))
                self.assertGreater(red, 200)
                self.assertLess(green, 30)
                self.assertLess(blue, 30)

    def test_partial_and_beyond_end_capture(self):
        out = self.root / 'partial'
        result = json.loads(self.run_cli('--output', out, '--times', '0,99', code=1))
        self.assertFalse(result['complete'])
        self.assertEqual(result['decoded'], 1)
        report = json.loads((out / 'frames.json').read_text())
        self.assertEqual(report['frames'][1]['status'], 'failed')
        self.assertTrue((out / 'frame-001.png').is_file())
        self.assertFalse((out / 'frame-002.png').exists())

    def test_invalid_video_has_failure_report(self):
        self.video.write_bytes(b'not a video')
        out = self.root / 'invalid-video'
        self.run_cli('--output', out, '--times', '0', code=1)
        report = json.loads((out / 'frames.json').read_text())
        self.assertFalse(report['complete'])
        self.assertEqual(report['frames'][0]['status'], 'failed')

    def test_existing_output_and_bad_times_are_rejected(self):
        out = self.root / 'existing'
        out.mkdir()
        marker = out / 'marker.txt'
        marker.write_text('preserve')
        self.run_cli('--output', out, '--times', '0', code=2)
        self.assertEqual(marker.read_text(), 'preserve')
        for index, value in enumerate(('nan', 'inf', '-1', '0,,1', 'text', ','.join(['0'] * 101))):
            target = self.root / str(index)
            self.run_cli('--output', target, '--times=' + value, code=2)
            self.assertFalse(target.exists())
        self.run_cli('--output', self.root / 'bad-offset', '--times', '0', '--source-start', 'nan', code=2)

    def test_missing_executable_is_not_success(self):
        out = self.root / 'missing-ffmpeg'
        self.run_cli('--output', out, '--times', '0', '--ffmpeg', self.root / 'missing-exe', code=1)
        self.assertFalse(json.loads((out / 'frames.json').read_text())['complete'])

    def test_successful_process_without_frames_is_failure(self):
        fake = self.root / 'fake-ffmpeg'
        fake.write_text('#!/bin/sh\nexit 0\n')
        fake.chmod(0o700)
        out = self.root / 'false-success'
        self.run_cli('--output', out, '--times', '0', '--ffmpeg', fake, code=1)
        self.assertFalse(json.loads((out / 'frames.json').read_text())['complete'])

    def test_input_protocols_exclude_network(self):
        from unittest.mock import patch
        out = self.root / 'offline'
        with patch.object(sys, 'argv', [str(SCRIPT), str(self.video), '--output', str(out),
                                        '--times', '0', '--ffmpeg', FFMPEG]):
            real_run = subprocess.run
            calls = []
            def inspect_run(command, **kwargs):
                calls.append(command)
                return real_run(command, **kwargs)
            with patch.object(module.subprocess, 'run', side_effect=inspect_run):
                self.assertEqual(module.main(), 0)
            command = calls[0]
            self.assertEqual(command[command.index('-protocol_whitelist') + 1], 'file,pipe')

    def test_png_requires_real_decode_not_just_crc(self):
        valid = self.root / 'valid.png'
        Image.new('RGB', (10, 8), (255, 0, 0)).save(valid)
        self.assertEqual(module.png_dimensions(valid), (10, 8))
        def chunk(kind, payload):
            return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
        # CRCs and deflate stream valid, but insufficient pixels for the declared size.
        malformed = self.root / 'insufficient.png'
        malformed.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 10, 8, 8, 2, 0, 0, 0))
                              + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00')) + chunk(b'IEND', b''))
        with self.assertRaises((OSError, ValueError)):
            module.png_dimensions(malformed)
        truncated = self.root / 'truncated.png'
        truncated.write_bytes(valid.read_bytes()[:40])
        with self.assertRaises((OSError, ValueError, SyntaxError)):
            module.png_dimensions(truncated)


if __name__ == '__main__':
    unittest.main()
