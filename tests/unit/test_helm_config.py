from unittest.mock import patch

import pytest

from helm_config.handler import (
    generate_helm_values,
    get_environment,
)


@pytest.mark.parametrize(
    "environment, expected_replica_count",
    [
        ("development", "1"),
        ("staging", "2"),
        ("production", "2"),
    ],
)
def test_generate_helm_values(environment, expected_replica_count):
    result = generate_helm_values(environment)

    assert result == {
        "replicaCount": expected_replica_count
    }


def test_generate_helm_values_invalid_environment():
    with pytest.raises(ValueError):
        generate_helm_values("invalid")


@patch("helm_config.handler.ssm_client")
def test_get_environment_reads_ssm_parameter(mock_ssm_client):
    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {
            "Value": "staging"
        }
    }

    result = get_environment("/platform/account/env")

    assert result == "staging"

    mock_ssm_client.get_parameter.assert_called_once_with(
        Name="/platform/account/env"
    )