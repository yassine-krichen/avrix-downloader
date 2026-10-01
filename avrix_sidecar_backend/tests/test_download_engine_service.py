import pytest

from app.contracts.queue import QueueCreateRequest, QueueItemStatus
from app.services import download_engine_service as engine_module
from app.services import download_errors
from app.services.queue_service import QueueService


class AlwaysFailingYoutubeDL:
    def __init__(self, opts):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download=False):
        return {"title": "Some video"}

    def download(self, urls):
        raise RuntimeError("ERROR: [youtube] abc: Video unavailable")


@pytest.fixture
def queue(tmp_path, monkeypatch):
    service = QueueService(tmp_path / "download_queue.json")
    monkeypatch.setattr(engine_module, "queue_service", service)
    return service


def add_item(queue, **overrides):
    fields = {
        "url": "https://youtube.com/watch?v=abc",
        "format_type": "mp3",
        "quality": "best",
        "download_path": "C:/downloads",
        **overrides,
    }
    return queue.add_item(QueueCreateRequest(**fields))


def test_failed_download_is_marked_failed_with_a_friendly_error_message(queue, monkeypatch):
    monkeypatch.setattr(download_errors.yt_dlp, "YoutubeDL", AlwaysFailingYoutubeDL)
    item = add_item(queue)

    engine_module.download_engine_service._run_download(item.id)

    failed = queue.get_item(item.id)
    assert failed.status == QueueItemStatus.FAILED
    assert "unavailable" in failed.error_message.lower()
    assert failed.title == "Some video"


def test_strict_video_without_ffmpeg_fails_the_item_instead_of_leaving_it_downloading(queue, monkeypatch):
    monkeypatch.setattr(engine_module, "resolve_ffmpeg_location", lambda: None)
    item = add_item(queue, format_type="mp4", download_policy="strict_quality")

    engine_module.download_engine_service._run_download(item.id)

    failed = queue.get_item(item.id)
    assert failed.status == QueueItemStatus.FAILED
    assert "ffmpeg" in failed.error_message


def test_retrying_a_failed_item_clears_its_previous_error(queue):
    item = add_item(queue)
    queue.update_item_fields(item.id, status=QueueItemStatus.FAILED, error_message="old error")

    queue.bulk_retry(retry_failed=True, retry_cancelled=False)

    retried = queue.get_item(item.id)
    assert retried.status == QueueItemStatus.PENDING
    assert retried.error_message is None
