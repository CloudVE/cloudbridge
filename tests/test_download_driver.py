"""
Provider-agnostic unit tests for the base ranged download driver
(``BaseBucketObject.download_to_file`` / ``_download_ranged``).

The driver is the engine behind transparent large downloads on providers that
do not override it (GCP, OpenStack Swift). Because the mock provider is
AWS-backed and AWS overrides the driver with boto3's native downloader, the
driver is exercised here directly against in-memory fakes so it has coverage
in CI without cloud credentials.
"""
import os
import tempfile
import threading
import unittest

from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.interfaces.exceptions import InvalidValueException
from cloudbridge.interfaces.resources import TransferConfig


class _Recorder:
    """Thread-safe range log shared by the original and cloned fake
    services."""

    def __init__(self, content):
        self.content = content
        self._lock = threading.Lock()
        self.ranges = []            # (offset, length) served
        self.services_used = set()  # id() of each service that served a range
        self.clone_count = 0
        self.single_shot = False
        self.active = 0
        self.max_active = 0
        self.fail_on_offset = None  # offset that should raise

    def serve_range(self, service, offset, length):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if self.fail_on_offset == offset:
                raise RuntimeError("boom at offset %d" % offset)
            # Hold briefly so concurrent fetches genuinely overlap.
            threading.Event().wait(0.02)
            with self._lock:
                self.ranges.append((offset, length))
                self.services_used.add(id(service))
            return self.content[offset:offset + length]
        finally:
            with self._lock:
                self.active -= 1


class _FakeService:
    def __init__(self, recorder, provider):
        self._recorder = recorder
        self._provider = provider

    def download_range(self, bucket, object_name, offset, length):
        return self._recorder.serve_range(self, offset, length)


class _FakeStorage:
    def __init__(self, service):
        self._bucket_objects = service


class _FakeProvider:
    def __init__(self, recorder):
        self._recorder = recorder
        self.storage = _FakeStorage(_FakeService(recorder, self))

    def clone(self, zone=None):
        self._recorder.clone_count += 1
        return _FakeProvider(self._recorder)

    def _get_config_value(self, key, default_value=None):
        return default_value


class _DriverObject(BaseBucketObject):
    """A BaseBucketObject wired to fakes with tiny transfer sizes."""

    def __init__(self, provider, threshold, part_size, concurrency):
        super(_DriverObject, self).__init__(provider)
        self._threshold = threshold
        self._part_size = part_size
        self._concurrency = concurrency

    @property
    def id(self):
        return "obj"

    @property
    def name(self):
        return "obj"

    @property
    def size(self):
        return len(self._provider._recorder.content)

    @property
    def bucket(self):
        return "BUCKET"

    def save_content(self, target_stream):
        self._provider._recorder.single_shot = True
        target_stream.write(self._provider._recorder.content)

    def _multipart_threshold(self, config=None):
        if config is not None and config.threshold is not None:
            return config.threshold
        return self._threshold

    def _multipart_part_size(self, config=None):
        if config is not None and config.part_size is not None:
            return config.part_size
        return self._part_size

    def _multipart_max_concurrency(self, config=None):
        if config is not None and config.max_concurrency is not None:
            return config.max_concurrency
        return self._concurrency


class DownloadDriverTestCase(unittest.TestCase):

    def _driver(self, recorder, threshold, part_size, concurrency):
        return _DriverObject(
            _FakeProvider(recorder), threshold, part_size, concurrency)

    def _download(self, driver, config=None):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.remove(path)
        try:
            driver.download_to_file(path, config)
            with open(path, 'rb') as f:
                return f.read()
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_reassembles_content_in_order(self):
        content = b"abcdefghijABCDEFGHIJ0123456789x"  # 31 bytes -> 8 ranges
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=10, part_size=4, concurrency=3)
        self.assertEqual(self._download(driver), content)
        self.assertFalse(recorder.single_shot)
        # Ranges tile the object exactly: no gaps, no overlap, short tail.
        self.assertEqual(
            sorted(recorder.ranges),
            [(offset, min(4, 31 - offset)) for offset in range(0, 31, 4)])

    def test_below_threshold_uses_single_shot(self):
        content = b"tiny content"
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=100, part_size=4, concurrency=3)
        self.assertEqual(self._download(driver), content)
        self.assertTrue(recorder.single_shot)
        self.assertEqual(recorder.ranges, [])

    def test_downloads_ranges_concurrently_via_cloned_services(self):
        concurrency = 4
        content = bytes(range(12))  # 12 ranges of one byte each
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=1, part_size=1, concurrency=concurrency)
        self.assertEqual(self._download(driver), content)

        # A clone per worker, reused across ranges.
        self.assertEqual(recorder.clone_count, concurrency)
        self.assertEqual(len(recorder.services_used), concurrency)
        # Real parallelism happened, bounded by the configured concurrency.
        self.assertGreater(recorder.max_active, 1)
        self.assertLessEqual(recorder.max_active, concurrency)

    def test_single_concurrency_does_not_clone(self):
        content = b"abcdefghij"
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=1, part_size=4, concurrency=1)
        self.assertEqual(self._download(driver), content)
        self.assertEqual(recorder.clone_count, 0)
        self.assertEqual(recorder.max_active, 1)

    def test_per_call_config_overrides_concurrency(self):
        content = bytes(range(12))
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=1, part_size=1, concurrency=1)
        result = None
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            driver.download_to_file(path, TransferConfig(max_concurrency=3))
            with open(path, 'rb') as f:
                result = f.read()
        finally:
            os.remove(path)
        self.assertEqual(result, content)
        self.assertEqual(recorder.clone_count, 3)
        self.assertGreater(recorder.max_active, 1)
        self.assertLessEqual(recorder.max_active, 3)

    def test_removes_partial_file_and_raises_on_range_failure(self):
        content = bytes(range(16))
        recorder = _Recorder(content)
        recorder.fail_on_offset = 8
        driver = self._driver(
            recorder, threshold=1, part_size=4, concurrency=2)
        fd, path = tempfile.mkstemp()
        os.close(fd)
        os.remove(path)
        try:
            with self.assertRaises(Exception):
                driver.download_to_file(path)
            self.assertFalse(os.path.exists(path))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_part_size_must_be_positive(self):
        content = bytes(range(16))
        recorder = _Recorder(content)
        driver = self._driver(
            recorder, threshold=1, part_size=4, concurrency=2)
        with self.assertRaises(InvalidValueException):
            self._download(driver, TransferConfig(part_size=0))
        self.assertEqual(recorder.ranges, [])


if __name__ == "__main__":
    unittest.main()
