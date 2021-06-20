import pytest
from tencentcos_storage.storage import TencentCOSStorage


@pytest.fixture
def storage():
    return TencentCOSStorage(
        bucket="test-bucket",
        config={
            "Region": "region",
            "SecretId": "********",
            "SecretKey": "********",
        },
    )
