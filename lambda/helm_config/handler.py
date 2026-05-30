import json
import logging
import os

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm_client = boto3.client("ssm")


ENVIRONMENT_HELM_CONFIG = {
    "development": {
        "replica_count": 1,
    },
    "staging": {
        "replica_count": 2,
    },
    "production": {
        "replica_count": 2,
    },
}


def get_environment(parameter_name: str) -> str:
    response = ssm_client.get_parameter(
        Name=parameter_name
    )

    return response["Parameter"]["Value"]


def generate_helm_values(environment: str) -> dict:
    if environment not in ENVIRONMENT_HELM_CONFIG:
        raise ValueError(
            f"Unsupported environment: {environment}"
        )

    return {
        "replicaCount": str(
            ENVIRONMENT_HELM_CONFIG[environment]["replica_count"]
        )
    }


def on_event(event, context):
    logger.info(json.dumps({
        "event": "helm_config_invoked",
        "request_type": event["RequestType"],
        "request_id": context.aws_request_id
    }))

    request_type = event["RequestType"]

    if request_type == "Delete":
        return {
            "PhysicalResourceId": "HelmConfigResource"
        }

    parameter_name = os.environ["PARAMETER_NAME"]

    environment = get_environment(parameter_name)

    helm_values = generate_helm_values(environment)

    return {
        "PhysicalResourceId": "HelmConfigResource",
        "Data": helm_values,
    }