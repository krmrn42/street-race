from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import to_plain_text

from streetrace.ui.completer import CommandCompleter, PathCompleter, PromptCompleter


# Helper function to simplify getting completion texts
def _get_completion_texts(
    completer: PathCompleter,
    text: str,
    cursor_offset: int = 0,
) -> list[str]:
    doc = Document(text, len(text) + cursor_offset)
    completions = list(completer.get_completions(doc, MagicMock()))
    return sorted([c.text for c in completions])


# Helper function to simplify getting completion displays
def _get_completion_displays(
    completer: PathCompleter,
    text: str,
    cursor_offset: int = 0,
) -> list[str]:
    doc = Document(text, len(text) + cursor_offset)
    completions = list(completer.get_completions(doc, MagicMock()))
    return sorted([to_plain_text(c.display) for c in completions])


class _FakePath:
    """Implements a fake directory structure.

    /fake/work
    /fake/work/src
    /fake/work/src/main.py
    /fake/work/README.md
    /fake/work/.hiddenfile
    """

    WORK_DIR = Path("/fake/work")

    @staticmethod
    def make_fake_is_dir(mock_is_dir: Callable[[Path], bool]) -> None:
        def fake_is_dir(path: Path) -> bool:
            return path.name in ["fake", "work", "src"] and path.parent.name in [
                "fake",
                "work",
            ]

        mock_is_dir.side_effect = fake_is_dir

    @staticmethod
    def make_fake_iterdir(mock_iterdir: Callable[[Path], Iterator[Path]]) -> None:
        def fake_iterdir(path: Path) -> Iterator[Path]:
            if path.name == "fake":
                yield from [path.joinpath(p) for p in ["work"]]
            elif path.name == "work":
                yield from [
                    path.joinpath(p) for p in ["src", "README.md", ".hiddenfile"]
                ]
            elif path.name == "src":
                yield from [path.joinpath(p) for p in ["main.py"]]

        mock_iterdir.side_effect = fake_iterdir

    @staticmethod
    def make_fake_iterdir_err(mock_iterdir: Callable[[Path], Iterator[Path]]) -> None:
        def fake_iterdir(_: Path) -> Iterator[Path]:
            raise OSError

        mock_iterdir.side_effect = fake_iterdir


class TestPathCompleter:
    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_oserr(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir_err(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        assert _get_completion_displays(completer, "@\n") == []
        assert _get_completion_displays(completer, "@src/") == []

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_not_a_path(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        assert _get_completion_displays(completer, "@\n") == []

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_not_a_mention(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        assert _get_completion_displays(completer, "src/") == []

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_not_a_dir(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        # Completions without a prefix should show non-hidden files/dirs
        assert _get_completion_texts(completer, "@src/abc/") == []
        assert _get_completion_texts(completer, "@src/abc/src") == []
        assert _get_completion_texts(completer, "@src/src") == []
        assert _get_completion_texts(completer, "@src/src/") == []
        assert _get_completion_texts(completer, "@abc/") == []
        assert _get_completion_texts(completer, "@README.md/") == []
        assert _get_completion_texts(completer, "@README.md/.") == []

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_missing_dot(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        # Completions without a prefix should show non-hidden files/dirs
        assert _get_completion_texts(completer, "@src/.") == []
        assert _get_completion_texts(completer, "@.") == [".hiddenfile"]

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_complete_root_files_and_dirs(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        # Completions without a prefix should show non-hidden files/dirs
        assert _get_completion_texts(completer, "@") == [
            "README.md",
            "src",
        ]
        # Filtering by prefix
        assert _get_completion_texts(completer, "@R") == ["README.md"]
        assert _get_completion_texts(completer, "@s") == ["src"]
        # Hidden files should be shown when the prefix starts with .
        assert _get_completion_texts(completer, "@.") == [".hiddenfile"]
        # Display text should have the slash for directories
        assert _get_completion_displays(completer, "@") == ["README.md", "src/"]

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.iterdir", autospec=True)
    def test_complete_subdirectory(
        self,
        mock_iterdir: Callable[[Path], Iterator[Path]],
        mock_is_dir: Callable[[Path], bool],
    ) -> None:
        # Mock is_dir method to always return True
        _FakePath.make_fake_is_dir(mock_is_dir)
        _FakePath.make_fake_iterdir(mock_iterdir)

        completer = PathCompleter(_FakePath.WORK_DIR)

        # Test completions for src directory
        assert _get_completion_texts(completer, "@src/") == ["src/main.py"]
        assert _get_completion_displays(completer, "@src/") == ["main.py"]
        assert _get_completion_texts(completer, "foo @src/") == ["src/main.py"]
        assert _get_completion_displays(completer, "foo @src/") == ["main.py"]

        # Test completions with partial prefix
        assert _get_completion_texts(completer, "@src/m") == ["src/main.py"]
        assert _get_completion_displays(completer, "@src/m") == ["main.py"]
        assert _get_completion_texts(completer, "bar @src/m") == ["src/main.py"]
        assert _get_completion_displays(completer, "bar @src/m") == ["main.py"]

    @patch("pathlib.Path.is_dir", autospec=True)
    def test_invalid_working_dir(self, mock_is_dir: Callable[[Path], bool]) -> None:
        mock_is_dir.return_value = False
        with pytest.raises(ValueError, match="not a valid directory"):
            PathCompleter(Path("/invalid/dir"))


class TestPromptCompleterComposition:
    @pytest.fixture
    def prompt_completer_setup(self):
        """Set up test environment for prompt completer tests."""
        mock_path_completer = MagicMock(spec=PathCompleter)
        mock_command_completer = MagicMock(spec=CommandCompleter)
        prompt_completer = PromptCompleter(
            [mock_path_completer, mock_command_completer],
        )
        return {
            "mock_path_completer": mock_path_completer,
            "mock_command_completer": mock_command_completer,
            "prompt_completer": prompt_completer,
        }

    def test_calls_both_delegates(self, prompt_completer_setup) -> None:
        mock_path_completer = prompt_completer_setup["mock_path_completer"]
        mock_command_completer = prompt_completer_setup["mock_command_completer"]
        prompt_completer = prompt_completer_setup["prompt_completer"]

        doc = Document("some text", len("some text"))
        event = MagicMock()
        mock_path_completer.get_completions.return_value = iter(
            [Completion("path_comp")],
        )
        mock_command_completer.get_completions.return_value = iter(
            [Completion("cmd_comp")],
        )
        completions = list(prompt_completer.get_completions(doc, event))
        mock_path_completer.get_completions.assert_called_once_with(doc, event)
        mock_command_completer.get_completions.assert_called_once_with(doc, event)
        completion_texts = sorted([c.text for c in completions])
        assert completion_texts == ["cmd_comp", "path_comp"]

    def test_works_if_one_delegate_returns_nothing(
        self,
        prompt_completer_setup,
    ) -> None:
        mock_path_completer = prompt_completer_setup["mock_path_completer"]
        mock_command_completer = prompt_completer_setup["mock_command_completer"]
        prompt_completer = prompt_completer_setup["prompt_completer"]

        doc = Document("@path", len("@path"))
        event = MagicMock()
        mock_path_completer.get_completions.return_value = iter(
            [Completion("path/comp1"), Completion("path/comp2")],
        )
        mock_command_completer.get_completions.return_value = iter([])
        completions = list(prompt_completer.get_completions(doc, event))
        mock_path_completer.get_completions.assert_called_once_with(doc, event)
        mock_command_completer.get_completions.assert_called_once_with(doc, event)
        completion_texts = sorted([c.text for c in completions])
        assert completion_texts == ["path/comp1", "path/comp2"]

    def test_works_if_command_delegate_returns_nothing(
        self,
        prompt_completer_setup,
    ) -> None:
        mock_path_completer = prompt_completer_setup["mock_path_completer"]
        mock_command_completer = prompt_completer_setup["mock_command_completer"]
        prompt_completer = prompt_completer_setup["prompt_completer"]

        doc = Document("/xyz", len("/xyz"))
        event = MagicMock()
        mock_path_completer.get_completions.return_value = iter([])
        mock_command_completer.get_completions.return_value = iter([])
        completions = list(prompt_completer.get_completions(doc, event))
        mock_path_completer.get_completions.assert_called_once_with(doc, event)
        mock_command_completer.get_completions.assert_called_once_with(doc, event)
        assert completions == []
