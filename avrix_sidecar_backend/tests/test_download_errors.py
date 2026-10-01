import pytest

from app.services import download_errors
from app.services.download_errors import DownloadCancelled, describe_download_error, run_ydl_attempts


class FakeYoutubeDL:
    """Stands in for yt_dlp.YoutubeDL; behavior is scripted per option set."""

    calls: list[dict] = []

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download=False):
        return {"title": "Fake title"}

    def download(self, urls):
        FakeYoutubeDL.calls.append(self.opts)
        outcome = self.opts.get("outcome")
        if isinstance(outcome, Exception):
            raise outcome


@pytest.fixture(autouse=True)
def fake_ydl(monkeypatch):
    FakeYoutubeDL.calls = []
    monkeypatch.setattr(download_errors.yt_dlp, "YoutubeDL", FakeYoutubeDL)


def test_first_successful_attempt_stops_the_loop_and_reports_info():
    infos: list[dict] = []

    run_ydl_attempts([{"name": "a"}, {"name": "b"}], "https://x", infos.append)

    assert [call["name"] for call in FakeYoutubeDL.calls] == ["a"]
    assert infos == [{"title": "Fake title"}]


def test_failed_attempt_falls_back_to_the_next_attempt():
    attempts = [{"name": "strict", "outcome": RuntimeError("HTTP Error 403")}, {"name": "loose"}]

    run_ydl_attempts(attempts, "https://x", lambda info: None)

    assert [call["name"] for call in FakeYoutubeDL.calls] == ["strict", "loose"]


def test_all_attempts_failing_raises_the_last_error():
    attempts = [
        {"outcome": RuntimeError("first")},
        {"outcome": RuntimeError("second")},
    ]

    with pytest.raises(RuntimeError, match="second"):
        run_ydl_attempts(attempts, "https://x", lambda info: None)


def test_cancellation_is_not_retried_with_the_next_attempt():
    attempts = [{"name": "a", "outcome": DownloadCancelled("stop")}, {"name": "b"}]

    with pytest.raises(DownloadCancelled):
        run_ydl_attempts(attempts, "https://x", lambda info: None)

    assert [call["name"] for call in FakeYoutubeDL.calls] == ["a"]


def test_bot_check_error_gets_a_sign_in_hint_and_keeps_the_original_detail():
    exc = RuntimeError("ERROR: [youtube] abc: Sign in to confirm you're not a bot")

    message = describe_download_error(exc)

    assert "sign-in or bot check" in message
    assert "Sign in to confirm" in message


def test_missing_ffmpeg_error_gets_an_ffmpeg_hint():
    message = describe_download_error(RuntimeError("Strict quality video download requires ffmpeg in PATH"))

    assert "ffmpeg is missing" in message


def test_unavailable_video_error_gets_an_unavailable_hint():
    message = describe_download_error(RuntimeError("ERROR: [youtube] abc: Video unavailable"))

    assert "unavailable" in message.lower()


def test_unknown_error_is_passed_through_without_the_error_prefix():
    assert describe_download_error(RuntimeError("ERROR: something odd")) == "something odd"


def test_error_message_drops_ansi_codes_and_traceback_lines():
    exc = RuntimeError("\x1b[0;31mERROR:\x1b[0m boom\nTraceback (most recent call last):\n  File x")

    message = describe_download_error(exc)

    assert message == "boom"


def test_error_message_is_truncated_to_a_bounded_length():
    message = describe_download_error(RuntimeError("x" * 5000))

    assert len(message) <= download_errors.MAX_ERROR_LENGTH
