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
                self.assertEqual(gif.n_frames, len(build_art.TYPING_TIMELINE))
                frames, durations = [], []
                for i in range(gif.n_frames):
                    gif.seek(i)
                    frames.append(gif.convert('RGB'))
                    durations.append(gif.info['duration'])
                self.assertEqual(durations, [ms for _,_,ms in build_art.TYPING_TIMELINE])
                self.assertEqual(sum(durations), 4960)
                self.assertIsNone(ImageChops.difference(frames[0], frames[-1]).getbbox())
                mask = Image.new('L', gif.size, 255)
                draw = ImageDraw.Draw(mask)
                for x0, y0, x1, y1 in build_art.PAW_BOXES:
                    draw.rectangle((x0, y0-10, x1-1, y1), fill=0)
                for frame in frames[1:]:
                    diff = ImageChops.difference(frames[0], frame).convert('L')
                    diff.paste(0, mask=ImageChops.invert(mask))
                    self.assertIsNone(diff.getbbox(), 'Pixels outside the paws changed')
                self.assertIsNotNone(ImageChops.difference(frames[0], frames[2]).getbbox())
                self.assertEqual((Path(directory)/'pompompurin_idle.gif').read_bytes(),
                                 (ROOT/'assets/pompompurin_idle.gif').read_bytes())
