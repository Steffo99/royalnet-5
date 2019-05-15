import pytest
import uuid
from royalnet.network.packages import Package


def test_package_serialization():
    pkg = Package("ciao",
                  source=str(uuid.uuid4()),
                  destination=str(uuid.uuid4()),
                  source_conv_id=str(uuid.uuid4()),
                  destination_conv_id=str(uuid.uuid4()))
    assert pkg == Package.from_dict(pkg.to_dict())
    assert pkg == Package.from_json_string(pkg.to_json_string())
    assert pkg == Package.from_json_bytes(pkg.to_json_bytes())
