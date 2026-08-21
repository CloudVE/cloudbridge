"""
Provider-agnostic unit tests for chunked streaming reads
(``BucketObject.iter_content`` / ``save_content``).

Every provider streams object content through ``iter_content``, but only the
configured test provider gets exercised by the object store service suite. The
chunk-size contract those implementations have to honour is pinned here
against in-memory fakes so it has coverage in CI without cloud credentials.
"""
import unittest
from io import BytesIO

from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.interfaces.exceptions import InvalidValueException


class _FakeProvider:
    def __init__(self, config=None, bucket_objects=None):
        self._config = config or {}
        self.storage = _FakeStorage(bucket_objects)

    def _get_config_value(self, key, default_value=None):
        return self._config.get(key, default_value)


class _FakeStorage:
    def __init__(self, bucket_objects=None):
        self._bucket_objects = bucket_objects


class _NoRangeService:
    def download_range(self, bucket, name, offset, length):
        raise AssertionError("no range should have been requested")


class _FakeAzureContainer:
    """Stands in for AzureBucket: AzureBucketObject reaches its blob client
    through ``container._bucket.get_blob_client(name)``."""

    def __init__(self, blob_client):
        self._bucket = self
        self._blob_client = blob_client

    def get_blob_client(self, name):
        return self._blob_client


class _FakeBlobProperties:
    def __init__(self, name):
        self.name = name


class _FakeSwiftContainer:
    name = "bucket"


class _StreamingObject(BaseBucketObject):
    """A BaseBucketObject that streams from an in-memory buffer."""

    def __init__(self, provider, content):
        super(_StreamingObject, self).__init__(provider)
        self._content = content
        self.chunk_sizes_seen = []

    @property
    def id(self):
        return "obj"

    @property
    def name(self):
        return "obj"

    @property
    def size(self):
        return len(self._content)

    @property
    def bucket(self):
        return "BUCKET"

    def iter_content(self, chunk_size=None):
        size = self._iter_chunk_size(chunk_size)
        self.chunk_sizes_seen.append(size)
        return (self._content[i:i + size]
                for i in range(0, len(self._content), size))


class IterChunkSizeTestCase(unittest.TestCase):
    """The resolver that turns an optional chunk_size into a concrete one."""

    def _obj(self, config=None, content=b""):
        return _StreamingObject(_FakeProvider(config), content)

    def test_defaults_to_class_constant_when_unset(self):
        obj = self._obj()
        self.assertEqual(obj._iter_chunk_size(),
                         BaseBucketObject.CB_ITER_CHUNK_SIZE)

    def test_default_is_one_mebibyte(self):
        # Large enough that per-chunk overhead disappears against network
        # throughput, small enough to stay cheap per concurrent stream.
        self.assertEqual(BaseBucketObject.CB_ITER_CHUNK_SIZE, 1024 * 1024)

    def test_provider_config_overrides_class_constant(self):
        obj = self._obj({'iter_chunk_size': 8192})
        self.assertEqual(obj._iter_chunk_size(), 8192)

    def test_explicit_argument_overrides_provider_config(self):
        obj = self._obj({'iter_chunk_size': 8192})
        self.assertEqual(obj._iter_chunk_size(4096), 4096)

    def test_rejects_zero_chunk_size(self):
        obj = self._obj()
        with self.assertRaises(InvalidValueException):
            obj._iter_chunk_size(0)

    def test_rejects_negative_chunk_size(self):
        obj = self._obj()
        with self.assertRaises(InvalidValueException):
            obj._iter_chunk_size(-1)


class SaveContentTestCase(unittest.TestCase):
    """save_content is defined in terms of iter_content."""

    def _obj(self, content, config=None):
        return _StreamingObject(_FakeProvider(config), content)

    def test_writes_whole_content_to_target_stream(self):
        content = bytes(range(256)) * 40
        obj = self._obj(content)
        target = BytesIO()
        obj.save_content(target)
        self.assertEqual(target.getvalue(), content)

    def test_passes_chunk_size_through_to_iter_content(self):
        obj = self._obj(b"x" * 100)
        obj.save_content(BytesIO(), chunk_size=16)
        self.assertEqual(obj.chunk_sizes_seen, [16])

    def test_uses_default_chunk_size_when_unset(self):
        obj = self._obj(b"x" * 10)
        obj.save_content(BytesIO())
        self.assertEqual(obj.chunk_sizes_seen,
                         [BaseBucketObject.CB_ITER_CHUNK_SIZE])

    def test_handles_empty_object(self):
        obj = self._obj(b"")
        target = BytesIO()
        obj.save_content(target)
        self.assertEqual(target.getvalue(), b"")

    def test_does_not_require_a_readable_iter_content(self):
        # iter_content promises Iterable[bytes] and nothing more; providers
        # that return a bare generator must still work with save_content.
        obj = self._obj(b"abc")
        self.assertFalse(hasattr(obj.iter_content(), 'read'))
        target = BytesIO()
        obj.save_content(target)
        self.assertEqual(target.getvalue(), b"abc")


class ProviderIterContentTestCase(unittest.TestCase):
    """
    The per-provider chunking loops.

    The object store service suite only ever exercises the one provider it is
    configured against - in CI, the AWS-backed mock - so the loops the other
    providers use to turn an SDK handle into sized chunks are pinned here
    against fake SDK objects instead.
    """

    def test_azure_reads_chunk_size_slices_from_one_download(self):
        from cloudbridge.providers.azure.resources import AzureBucketObject

        content = bytes(range(256)) * 40   # 10 KiB, newline-free by design
        reads = []
        downloads = []

        class _Downloader:
            def __init__(self):
                self.offset = 0

            def read(self, size):
                reads.append(size)
                data = content[self.offset:self.offset + size]
                self.offset += len(data)
                return data

        class _BlobClient:
            def download_blob(self):
                downloads.append(1)
                return _Downloader()

        obj = AzureBucketObject(
            _FakeProvider(), _FakeAzureContainer(_BlobClient()),
            _FakeBlobProperties("obj"))

        chunks = list(obj.iter_content(chunk_size=1024))

        self.assertEqual(b"".join(chunks), content)
        self.assertEqual([len(c) for c in chunks], [1024] * 10)
        self.assertEqual(set(reads), {1024},
                         "Chunk size must be passed straight to read().")
        self.assertEqual(len(downloads), 1,
                         "The whole object should stream from a single "
                         "download, not one request per chunk.")

    def test_azure_uses_resolved_default_chunk_size(self):
        from cloudbridge.providers.azure.resources import AzureBucketObject

        reads = []

        class _Downloader:
            def read(self, size):
                reads.append(size)
                return b""

        class _BlobClient:
            def download_blob(self):
                return _Downloader()

        obj = AzureBucketObject(
            _FakeProvider({'iter_chunk_size': 4096}),
            _FakeAzureContainer(_BlobClient()), _FakeBlobProperties("obj"))

        self.assertEqual(list(obj.iter_content()), [])
        self.assertEqual(reads, [4096])

    def test_gcp_fetches_successive_ranges_of_chunk_size(self):
        from cloudbridge.providers.gcp.resources import GCPBucketObject

        content = bytes(range(256)) * 40   # 10 KiB
        ranges = []

        class _BucketObjects:
            def download_range(self, bucket, name, offset, length):
                ranges.append((offset, length))
                return content[offset:offset + length]

        obj = GCPBucketObject(
            _FakeProvider(bucket_objects=_BucketObjects()), "BUCKET",
            {'name': 'obj', 'size': str(len(content))})

        chunks = list(obj.iter_content(chunk_size=4096))

        self.assertEqual(b"".join(chunks), content)
        self.assertEqual(
            ranges, [(0, 4096), (4096, 4096), (8192, 2048)],
            "Ranges must tile the object exactly and the last must be "
            "clamped to the object size, not overrun it.")

    def test_gcp_reads_nothing_for_an_empty_object(self):
        from cloudbridge.providers.gcp.resources import GCPBucketObject

        obj = GCPBucketObject(
            _FakeProvider(bucket_objects=_NoRangeService()), "BUCKET",
            {'name': 'obj', 'size': '0'})
        self.assertEqual(list(obj.iter_content()), [])

    def test_gcp_rejects_bad_chunk_size_before_any_request(self):
        from cloudbridge.providers.gcp.resources import GCPBucketObject

        obj = GCPBucketObject(
            _FakeProvider(bucket_objects=_NoRangeService()), "BUCKET",
            {'name': 'obj', 'size': '100'})
        with self.assertRaises(InvalidValueException):
            obj.iter_content(chunk_size=0)

    def test_openstack_passes_chunk_size_as_resp_chunk_size(self):
        from cloudbridge.providers.openstack.resources import (
            OpenStackBucketObject)

        calls = []

        class _Swift:
            def get_object(self, container, name, resp_chunk_size=None):
                calls.append(resp_chunk_size)
                return {}, iter([b"data"])

        provider = _FakeProvider()
        provider.swift = _Swift()
        obj = OpenStackBucketObject(
            provider, _FakeSwiftContainer(), {'name': 'obj'})

        self.assertEqual(list(obj.iter_content(chunk_size=8192)), [b"data"])
        self.assertEqual(calls, [8192],
                         "resp_chunk_size is what makes swiftclient stream "
                         "rather than return the whole object.")


if __name__ == "__main__":
    unittest.main()
