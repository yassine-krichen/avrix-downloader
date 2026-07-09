import pytest

from app.contracts.queue import QueueCreateRequest, QueueItemStatus
from app.core.errors import AppError
from app.services.queue_service import QueueService


@pytest.fixture
def queue(tmp_path):
    return QueueService(tmp_path / "download_queue.json")


def make_request(url="https://youtube.com/watch?v=abc", **overrides):
    fields = {
        "url": url,
        "format_type": "mp4",
        "quality": "1080p",
        "download_path": "C:/downloads",
        **overrides,
    }
    return QueueCreateRequest(**fields)


def test_add_item_persists_and_round_trips_through_a_new_instance(tmp_path):
    file_path = tmp_path / "download_queue.json"
    queue = QueueService(file_path)

    added = queue.add_item(make_request())

    reloaded = QueueService(file_path)
    items = reloaded.list_items()
    assert len(items) == 1
    assert items[0].id == added.id
    assert items[0].status == QueueItemStatus.PENDING


def test_add_item_rejects_duplicate_active_url_and_format(queue):
    queue.add_item(make_request())

    with pytest.raises(AppError) as exc_info:
        queue.add_item(make_request())

    assert exc_info.value.status_code == 409


def test_add_item_allows_same_url_with_different_quality(queue):
    queue.add_item(make_request(quality="1080p"))
    second = queue.add_item(make_request(quality="720p"))

    assert len(queue.list_items()) == 2
    assert second.quality == "720p"


def test_add_item_allows_duplicate_url_once_prior_item_finished(queue):
    first = queue.add_item(make_request())
    queue.update_item_fields(first.id, status=QueueItemStatus.COMPLETED)

    second = queue.add_item(make_request())

    assert len(queue.list_items()) == 2
    assert second.status == QueueItemStatus.PENDING


def test_remove_item_drops_it_from_the_queue(queue):
    item = queue.add_item(make_request())

    queue.remove_item(item.id)

    assert queue.list_items() == []


def test_remove_item_raises_not_found_for_unknown_id(queue):
    with pytest.raises(AppError) as exc_info:
        queue.remove_item("does-not-exist")

    assert exc_info.value.status_code == 404


def test_move_item_up_swaps_with_previous(queue):
    first = queue.add_item(make_request(url="https://youtube.com/watch?v=a"))
    second = queue.add_item(make_request(url="https://youtube.com/watch?v=b"))

    result = queue.move_item(second.id, "up")

    assert [item.id for item in result] == [second.id, first.id]


def test_move_item_up_at_top_is_a_no_op(queue):
    first = queue.add_item(make_request(url="https://youtube.com/watch?v=a"))
    second = queue.add_item(make_request(url="https://youtube.com/watch?v=b"))

    result = queue.move_item(first.id, "up")

    assert [item.id for item in result] == [first.id, second.id]


def test_move_item_down_at_bottom_is_a_no_op(queue):
    first = queue.add_item(make_request(url="https://youtube.com/watch?v=a"))
    second = queue.add_item(make_request(url="https://youtube.com/watch?v=b"))

    result = queue.move_item(second.id, "down")

    assert [item.id for item in result] == [first.id, second.id]


def test_clear_finished_keeps_only_active_items(queue):
    pending = queue.add_item(make_request(url="https://youtube.com/watch?v=a"))
    completed = queue.add_item(make_request(url="https://youtube.com/watch?v=b"))
    failed = queue.add_item(make_request(url="https://youtube.com/watch?v=c"))
    cancelled = queue.add_item(make_request(url="https://youtube.com/watch?v=d"))
    queue.update_item_fields(completed.id, status=QueueItemStatus.COMPLETED)
    queue.update_item_fields(failed.id, status=QueueItemStatus.FAILED)
    queue.update_item_fields(cancelled.id, status=QueueItemStatus.CANCELLED)

    remaining = queue.clear_finished()

    assert [item.id for item in remaining] == [pending.id]


def test_clear_all_empties_the_queue(queue):
    queue.add_item(make_request())

    queue.clear_all()

    assert queue.list_items() == []


def test_bulk_retry_resets_failed_items_to_pending(queue):
    item = queue.add_item(make_request())
    queue.update_item_fields(item.id, status=QueueItemStatus.FAILED, progress=42.0)

    queue.bulk_retry(retry_failed=True, retry_cancelled=False)

    reloaded = queue.get_item(item.id)
    assert reloaded.status == QueueItemStatus.PENDING
    assert reloaded.progress == 0.0


def test_bulk_retry_leaves_cancelled_items_when_not_requested(queue):
    item = queue.add_item(make_request())
    queue.update_item_fields(item.id, status=QueueItemStatus.CANCELLED)

    queue.bulk_retry(retry_failed=True, retry_cancelled=False)

    assert queue.get_item(item.id).status == QueueItemStatus.CANCELLED


def test_find_next_pending_skips_excluded_ids_and_urls(queue):
    first = queue.add_item(make_request(url="https://youtube.com/watch?v=a"))
    second = queue.add_item(make_request(url="https://youtube.com/watch?v=b"))

    result = queue.find_next_pending(excluded_ids={first.id})
    assert result.id == second.id

    result = queue.find_next_pending(excluded_ids=set(), excluded_urls={first.url})
    assert result.id == second.id


def test_find_next_pending_returns_none_when_all_excluded(queue):
    item = queue.add_item(make_request())

    result = queue.find_next_pending(excluded_ids={item.id})

    assert result is None
