import io

import pytest

from django.core.files.base import File
from qcloud_cos.cos_exception import CosServiceError
from unittest.mock import MagicMock
from qcloud_cos.cos_client import CosS3Client, CosConfig
from django.core.exceptions import SuspiciousFileOperation
from django.core.exceptions import ImproperlyConfigured
from tencentcos_storage.storage import TencentCOSStorage
from django.core.files.storage import Storage


class TestTencentCOSStorage:
    def test_setting_without_bucket(self):
        with pytest.raises(ImproperlyConfigured):
            TencentCOSStorage()

    def test_setting_with_bucket(self, settings):
        settings.TENCENTCOS_STORAGE = {
            "BUCKET": "test-bucket",
            "CONFIG": {
                "Region": "region",
                "SecretId": "********",
                "SecretKey": "********",
            },
        }
        storage = TencentCOSStorage()
        assert storage.bucket == "test-bucket"

    def test_setting_miss_required_config_kwargs(self, settings):
        settings.TENCENTCOS_STORAGE = {
            "BUCKET": "test-bucket",
            "CONFIG": {
                "Region": "region",
            },
        }
        with pytest.raises(ImproperlyConfigured):
            TencentCOSStorage()

    def test_normalize_root_path(self):
        storage = TencentCOSStorage(
            bucket="test-bucket",
            root_path="/namespace",
            config={
                "Region": "region",
                "SecretId": "********",
                "SecretKey": "********",
            },
        )
        assert storage.root_path == "/namespace/"

    def test_delete(self, monkeypatch, storage):
        mm = MagicMock(return_value=None)
        monkeypatch.setattr(CosS3Client, "delete_object", mm)
        assert storage.delete("test-file") is None

    def test_exists(self, monkeypatch, storage):
        mm = MagicMock(return_value={"foo": "bar"})
        monkeypatch.setattr(CosS3Client, "head_object", mm)
        assert storage.exists("test-file") is True

    def test_does_not_exists(self, monkeypatch, storage):
        mm = MagicMock(
            side_effect=CosServiceError(
                method="", message={"code": "NoSuchResource"}, status_code=404
            ),
        )
        monkeypatch.setattr(CosS3Client, "head_object", mm)
        assert storage.exists("nonexistence-file") is False

    def test_exists_raise_exception(self, monkeypatch, storage):
        mm = MagicMock(
            side_effect=CosServiceError(
                method="", message={"code": "Denied"}, status_code=403
            )
        )
        monkeypatch.setattr(CosS3Client, "head_object", mm)
        with pytest.raises(CosServiceError):
            storage.exists("test-file")

    def test_listdir_not_truncated(self, monkeypatch, storage):
        mm = MagicMock(
            return_value={
                "Contents": [
                    {"Key": "dir1/"},
                    {"Key": "dir2/"},
                    {"Key": "file1"},
                    {"Key": "file2"},
                ],
                "IsTruncated": "false",
            },
        )
        monkeypatch.setattr(CosS3Client, "list_objects", mm)
        dirs, files = storage.listdir("")
        assert dirs == ["dir1/", "dir2/"]
        assert files == ["file1", "file2"]

    def test_listdir_truncated(self, monkeypatch, storage):
        mm = MagicMock(
            side_effect=[
                {
                    "Contents": [
                        {"Key": "dir1/"},
                        {"Key": "file1"},
                    ],
                    "IsTruncated": "true",
                    "NextMarker": 2,
                },
                {
                    "Contents": [
                        {"Key": "dir2/"},
                        {"Key": "file2"},
                    ],
                    "IsTruncated": "false",
                },
            ],
        )
        monkeypatch.setattr(CosS3Client, "list_objects", mm)
        dirs, files = storage.listdir("")
        assert dirs == ["dir1/", "dir2/"]
        assert files == ["file1", "file2"]
        assert mm.call_count == 2

    def test_size(self, monkeypatch, storage):
        mm = MagicMock(return_value={"Content-Length": 10})
        monkeypatch.setattr(CosS3Client, "head_object", mm)
        assert storage.size("test-file") == 10

    def test_modified_time_not_implemented(self, storage):
        with pytest.raises(NotImplementedError):
            storage.get_modified_time("test-file")

    def test_accessed_time_not_implemented(self, storage):
        with pytest.raises(NotImplementedError):
            storage.get_accessed_time("test-file")

    def test__open(self, storage):
        obj = storage._open("file")
        assert isinstance(obj, File)

    def test__save(self, monkeypatch, storage):
        mm = MagicMock(return_value=None)
        monkeypatch.setattr(CosS3Client, "upload_file_from_buffer", mm)
        storage._save("file", File(io.BytesIO(b"bar"), "foo"))
        assert mm.called

    def test_url(self, monkeypatch, storage):
        mm = MagicMock()
        monkeypatch.setattr(CosConfig, "uri", mm)
        storage.url("test")
        mm.assert_called()
        mm.assert_called_with(bucket=storage.bucket, path="/test")

    def test__full_path(self, storage):
        assert storage._full_path("/") == "/"
        assert storage._full_path("") == "/"
        assert storage._full_path(".") == "/"
        assert storage._full_path("..") == "/"
        assert storage._full_path("../..") == "/"

        storage.root_path = "/namespace"
        assert storage._full_path("/") == "/namespace"
        assert storage._full_path("") == "/namespace"
        assert storage._full_path(".") == "/namespace"

        with pytest.raises(SuspiciousFileOperation):
            assert storage._full_path("..") == "/namespace"
        with pytest.raises(SuspiciousFileOperation):
            assert storage._full_path("../..") == "/namespace"

    def test_get_available_name(self, monkeypatch, storage):
        mm1 = MagicMock()
        mm2 = MagicMock()
        monkeypatch.setattr(TencentCOSStorage, "_full_path", mm1)
        monkeypatch.setattr(Storage, "get_available_name", mm2)
        storage.get_available_name("test")
        mm1.assert_called()
        mm2.assert_called()
