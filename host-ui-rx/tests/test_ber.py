"""No-hardware regression tests for the XCOM RX BER calculation."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
from bridge import compare_files


class TestCompareFiles(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def files(self, received, reference):
        a = Path(self.folder.name) / 'received.bin'
        b = Path(self.folder.name) / 'reference.bin'
        a.write_bytes(received)
        b.write_bytes(reference)
        return str(a), str(b)

    def test_identical_files(self):
        stats = compare_files(*self.files(b'\x00\xff\x5a', b'\x00\xff\x5a'))
        self.assertEqual(stats['bits_compared'], 24)
        self.assertEqual(stats['differing_bits'], 0)
        self.assertEqual(stats['bit_error_rate'], 0)

    def test_single_bit_error(self):
        stats = compare_files(*self.files(b'\x01\x00', b'\x00\x00'))
        self.assertEqual(stats['differing_bytes'], 1)
        self.assertEqual(stats['differing_bits'], 1)
        self.assertEqual(stats['bit_error_rate'], 1 / 16)

    def test_mismatched_lengths_rejected_even_if_extra_bytes_are_zero(self):
        a, b = self.files(b'\x01', b'\x01\x00')
        with self.assertRaisesRegex(ValueError, 'File size mismatch'):
            compare_files(a, b)

    def test_empty_files_rejected(self):
        with self.assertRaisesRegex(ValueError, 'empty'):
            compare_files(*self.files(b'', b''))

    def test_chunk_boundary(self):
        a, b = self.files(b'\x00\xff\x00', b'\x00\x00\x01')
        stats = compare_files(a, b, chunk_size=2)
        self.assertEqual(stats['differing_bits'], 9)
        self.assertEqual(stats['differing_bytes'], 2)


if __name__ == '__main__':
    unittest.main()
