"""
Provider-agnostic unit tests for the base multipart upload driver
(``BaseBucketObject._upload_multipart``).

The driver is the engine behind transparent large uploads on providers that do
not override it (GCP, OpenStack Swift). Because the mock provider is AWS-backed
and AWS overrides the driver with boto3's native uploader, the driver is
exercised here directly against in-memory fakes so it has coverage in CI
without cloud credentials.
"""
import threading
import unittest
from io import BytesIO

from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.base.resources import BaseMultipartUpload
from cloudbridge.base.resources import BaseUploadPart
from cloudbridge.interfaces.exceptions import InvalidValueException


class _Recorder:
    """Thread-safe sink shared by the original and all cloned fake services."""

    def __init__(self):
        self._lock = threading.Lock()
        self.parts = {}            # part_number -> bytes
        self.services_used = set()  # id() of each service that uploaded a part
        self.clone_count = 0
        self.completed_order = None
        self.aborted = False
        self.active = 0
        self.max_active = 0
        self.fail_on_part = None    # part_number that should raise

    def record_part(self, service, part_number, data):
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if self.fail_on_part == part_number:
                raise RuntimeError("boom on part %d" % part_number)
            # Hold briefly so concurrent uploads genuinely overlap.
            time_to_sleep = 0.02
            _sleep(time_to_sleep)
            with self._lock:
                self.parts[part_number] = bytes(data)
                self.services_used.add(id(service))
        finally:
            with self._lock:
                self.active -= 1


def _sleep(seconds):
    # Indirection so the deterministic tests can monkeypatch if needed; a plain
    # sleep is fine here and keeps the overlap window small.
    threading.Event().wait(seconds)


class _FakeService:
    def __init__(self, recorder, provider):
        self._recorder = recorder
        self._provider = provider

    def create_multipart_upload(self, bucket, object_name):
        return BaseMultipartUpload(self._provider, bucket, object_name, "upl")

    def upload_part(self, bucket, upload, part_number, data):
        self._recorder.record_part(self, part_number, data)
        return BaseUploadPart(part_number, "etag-%d" % part_number)

    def complete_multipart_upload(self, bucket, upload, parts):
        ordered = sorted(parts, key=lambda p: p.part_number)
        self._recorder.completed_order = [p.part_number for p in ordered]
        return b"".join(self._recorder.parts[p.part_number] for p in ordered)

    def abort_multipart_upload(self, bucket, upload):
        self._recorder.aborted = True


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
    """A BaseBucketObject wired to fakes, with a tiny minimum part size so
    tests can use small payloads."""

    CB_MULTIPART_MIN_PART_SIZE = 1

    def __init__(self, provider, part_size, concurrency):
        super(_DriverObject, self).__init__(provider)
        self._part_size = part_size
        self._concurrency = concurrency

    @property
    def id(self):
        return "obj"

    @property
    def name(self):
        return "obj"

    @property
    def bucket(self):
        return "BUCKET"

    @property
    def _multipart_part_size(self):
        return self._part_size

    @property
    def _multipart_max_concurrency(self):
        return self._concurrency


class MultipartDriverTestCase(unittest.TestCase):

    def _driver(self, recorder, part_size, concurrency):
        return _DriverObject(_FakeProvider(recorder), part_size, concurrency)

    def test_reassembles_payload_in_order(self):
        recorder = _Recorder()
        driver = self._driver(recorder, part_size=4, concurrency=3)
        content = b"abcdefghijABCDEFGHIJ0123456789x"  # 31 bytes -> 8 parts
        result = driver._upload_multipart(BytesIO(content))
        self.assertEqual(result, content)
        self.assertEqual(recorder.completed_order, list(range(1, 9)))
        # Final part is the short remainder (3 bytes).
        self.assertEqual(recorder.parts[8], content[28:])

    def test_handles_short_reads_without_undersized_parts(self):
        recorder = _Recorder()
        driver = self._driver(recorder, part_size=8, concurrency=2)

        class _DripStream:
            """Returns at most 3 bytes per read to simulate a socket-like
            stream; the driver must coalesce reads up to the part size."""
            def __init__(self, data):
                self._buf = BytesIO(data)

            def read(self, size):
                return self._buf.read(min(size, 3))

        content = bytes(range(20))  # 20 bytes, part_size 8 -> 8,8,4
        result = driver._upload_multipart(_DripStream(content))
        self.assertEqual(result, content)
        self.assertEqual(len(recorder.parts[1]), 8)
        self.assertEqual(len(recorder.parts[2]), 8)
        self.assertEqual(len(recorder.parts[3]), 4)

    def test_uploads_parts_concurrently_via_cloned_services(self):
        recorder = _Recorder()
        concurrency = 4
        driver = self._driver(recorder, part_size=1, concurrency=concurrency)
        # 12 parts (one byte each) across a pool of 4 clones.
        content = b"0123456789ab"
        driver._upload_multipart(BytesIO(content))

        # A clone per worker, reused across parts.
        self.assertEqual(recorder.clone_count, concurrency)
        self.assertEqual(len(recorder.services_used), concurrency)
        # Real parallelism happened, bounded by the configured concurrency.
        self.assertGreater(recorder.max_active, 1)
        self.assertLessEqual(recorder.max_active, concurrency)

    def test_single_concurrency_does_not_clone(self):
        recorder = _Recorder()
        driver = self._driver(recorder, part_size=4, concurrency=1)
        driver._upload_multipart(BytesIO(b"abcdefghij"))
        self.assertEqual(recorder.clone_count, 0)
        self.assertEqual(recorder.max_active, 1)

    def test_aborts_and_raises_on_part_failure(self):
        recorder = _Recorder()
        recorder.fail_on_part = 2
        driver = self._driver(recorder, part_size=4, concurrency=3)
        with self.assertRaises(Exception):
            driver._upload_multipart(BytesIO(b"abcdefghijklmnop"))
        self.assertTrue(recorder.aborted)

    def test_part_size_below_minimum_raises(self):
        recorder = _Recorder()
        # Use the real minimum here (not the test override) by going through a
        # driver whose part size is one below the production floor.
        driver = _DriverObject(_FakeProvider(recorder), part_size=4,
                               concurrency=2)
        driver.CB_MULTIPART_MIN_PART_SIZE = 5
        with self.assertRaises(InvalidValueException):
            driver._upload_multipart(BytesIO(b"abc"))
        # Nothing should have been created before validation failed.
        self.assertEqual(recorder.completed_order, None)


if __name__ == "__main__":
    unittest.main()
