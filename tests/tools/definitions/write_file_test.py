import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

# Assuming read_file also returns a tuple (content, msg)
from streetrace.tools.definitions.read_file import read_file
from streetrace.tools.definitions.write_file import write_utf8_file


class TestWriteFile(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        # Store relative paths for assertions
        self.test_file_rel = "test_file.txt"
        self.test_binary_rel = "test_binary.bin"
        self.test_latin1_rel = "test_latin1.txt"
        self.nested_file_rel = Path("nested") / "dirs" / "file.txt"
        self.test_type_rel = "test_type.txt"
        self.round_trip_rel = "round_trip.txt"

    def tearDown(self) -> None:
        # Clean up temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_write_text_file(self) -> None:
        """Test writing a simple text file."""
        abs_path = self.temp_dir / self.test_file_rel
        content = "This is a test file content."

        # Write the file
        rel_path = write_utf8_file(str(abs_path), content, self.temp_dir)
        assert rel_path == self.test_file_rel

        # Verify the file was written correctly
        assert abs_path.read_text() == content

    def test_create_directory(self) -> None:
        """Test that directories are created if they don't exist."""
        abs_path = self.temp_dir / self.nested_file_rel
        content = "File in nested directories"

        # This should create the necessary directories
        rel_path = write_utf8_file(str(abs_path), content, self.temp_dir)
        assert rel_path == str(self.nested_file_rel)

        # Verify the file was written
        assert abs_path.exists()
        assert abs_path.read_text() == content

    def test_security_restriction(self) -> None:
        """Test that writing outside work_dir is prevented."""
        # Try to write to a path outside the allowed root
        parent_dir = self.temp_dir.parent
        # Use an absolute path outside temp_dir to be sure
        outside_path = parent_dir / "outside_file.txt"

        with pytest.raises(
            ValueError,
            match="location outside the allowed working directory",
        ) as context:
            write_utf8_file(str(outside_path), "Should not write this", self.temp_dir)

        assert "Security error" in str(context.value)
        # Updated assertion message
        assert "outside the allowed working directory" in str(context.value)
        assert not outside_path.exists()

    def test_round_trip(self) -> None:
        """Test writing and then reading back a file with special encoding."""
        abs_path = self.temp_dir / self.round_trip_rel
        content = "Unicode text: こんにちは, 你好, Привет"
        encoding = "utf-8"

        # Write the file with specific encoding
        write_utf8_file(str(abs_path), content, self.temp_dir)

        # Read it back with the same encoding using the read_file function
        # Assuming read_file returns (content, msg)
        read_content = read_file(
            str(abs_path),
            self.temp_dir,
            encoding=encoding,
        )

        # Verify content is preserved
        assert read_content == content


if __name__ == "__main__":
    unittest.main()
