from io import BytesIO
from django.core.files.base import File


class TencentCOSFile(File):
    def __init__(self, name, storage):
        self.name = name
        self._storage = storage
        self._file = None

    @property
    def file(self):
        if self._file is None:
            response = self._storage.client.get_object(
                Bucket=self._storage.bucket,
                Key=self.name,
            )
            # >>> type(raw_stream)
            # <class 'urllib3.response.HTTPResponse'>
            raw_stream = response["Body"].get_raw_stream()
            self._file = BytesIO(raw_stream.data)
            self._file.seek(0)
        return self._file

    @file.setter
    def file(self, value):
        self._file = value
