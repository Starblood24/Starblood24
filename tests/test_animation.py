"""Optional local Pillow checks; daily stats workflow stays standard-library only."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
try:
    from PIL import Image, ImageChops, ImageDraw
    import build_art
except ImportError:
    Image = None


@unittest.skipIf(Image is None, 'Pillow is only required for local animation builds')
class AnimationTests(unittest.TestCase):
    def test_rebuild_timing_loop_palette_and_unchanged_portrait(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(build_art, 'OUTPUT', Path(directory)):
                build_art.build_gif()
            with Image.open(Path(directory)/'pompompurin_idle.gif') as gif:
                self.assertEqual(gif.info['loop'], 0)
                self.assertEqual(gif.n_frames, len(build_art.BLINK_LEVELS))
                frames, durations = [], []
                for i in range(gif.n_frames):
                    gif.seek(i)
                    frames.append(gif.convert('RGB'))
                    durations.append(gif.info['duration'])
                self.assertEqual(durations, list(build_art.BLINK_DURATIONS))
                self.assertEqual(sum(durations), 4000)
                self.assertIsNone(ImageChops.difference(frames[0], frames[-1]).getbbox())
                mask = Image.new('L', gif.size, 255)
                draw = ImageDraw.Draw(mask)
                for x0, y0, x1, y1 in build_art.EYE_BOXES:
                    draw.rectangle((x0, y0, x1-1, y1-1), fill=0)
                for frame in frames[1:]:
                    diff = ImageChops.difference(frames[0], frame).convert('L')
                    diff.paste(0, mask=ImageChops.invert(mask))
                    self.assertIsNone(diff.getbbox(), 'Pixels outside the eyes changed')
                self.assertIsNotNone(ImageChops.difference(frames[0], frames[4]).getbbox())
