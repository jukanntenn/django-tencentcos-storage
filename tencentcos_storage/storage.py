from django.conf import settings
from django.core.files.storage import Storage
from django.utils._os import safe_join
from django.utils.deconstruct import deconstructible
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError
from django.core.exceptions import ImproperlyConfigured
from .file import TencentCOSFile


@deconstructible
class TencentCOSStorage(Storage):
    """Tencent Cloud Object Storage class for Django pluggable storage system."""

    def __init__(self, bucket=None, root_path=None, config=None):
        setting = getattr(settings, "TENCENTCOS_STORAGE", {})
        self.bucket = bucket or setting.get("BUCKET", None)
        if self.bucket is None:
            raise ImproperlyConfigured("Must configure bucket.")

        self.root_path = root_path or setting.get("ROOT_PATH", "/")
        if not self.root_path.endswith("/"):
            self.root_path += "/"

        config_kwargs = config or setting.get("CONFIG", {})
        required = ["Region", "SecretId", "SecretKey"]
        for key in required:
            if key not in config_kwargs:
                raise ImproperlyConfigured("{key} is required.".format(key=key))

        config = CosConfig(**config_kwargs)
        self.client = CosS3Client(config)

    def _full_path(self, name):
        if name == "/":
            name = ""
        return safe_join(self.root_path, name).replace("\\", "/")

    def delete(self, name):
        self.client.delete_object(Bucket=self.bucket, Key=self._full_path(name))

    def exists(self, name):
        try:
            return bool(
                self.client.head_object(Bucket=self.bucket, Key=self._full_path(name))
            )
        except CosServiceError as e:
            if e.get_status_code() == 404 and e.get_error_code() == "NoSuchResource":
                return False
            raise

    def listdir(self, path):
        directories, files = [], []
        full_path = self._full_path(path)

        if full_path == "/":
            full_path = ""

        contents = []
        marker = ""
        while True:
            # return max 1000 objects every call
            response = self.client.list_objects(
                Bucket=self.bucket, Prefix=full_path.lstrip("/"), Marker=marker
            )
            contents.extend(response["Contents"])
            if response["IsTruncated"] == "false":
                break
            marker = response["NextMarker"]

        for entry in contents:
            if entry["Key"].endswith("/"):
                directories.append(entry["Key"])
            else:
                files.append(entry["Key"])
        # directories includes path itself
        return directories, files

    def size(self, name):
        head = self.client.head_object(Bucket=self.bucket, Key=self._full_path(name))
        return head["Content-Length"]

    def get_modified_time(self, name):
        # Not implement now
        return super().get_modified_time(name)

    def get_accessed_time(self, name):
        # Not implement now
        return super().get_accessed_time(name)

    def url(self, name):
        return self.client.get_conf().uri(
            bucket=self.bucket, path=self._full_path(name)
        )

    def _open(self, name, mode="rb"):
        return TencentCOSFile(self._full_path(name), self)

    def _save(self, name, content):
        self.client.upload_file_from_buffer(
            Bucket=self.bucket,
            Key=self._full_path(name),
            Body=content,
            PartSize=5,
            MAXThread=10,
        )
        return name

    def get_available_name(self, name, max_length=None):
        name = self._full_path(name)
        return super().get_available_name(name, max_length)
