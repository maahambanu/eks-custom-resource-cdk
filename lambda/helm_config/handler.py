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
    logger.info(
        json.dumps(
            {
                "event": "ssm_get_parameter_started",
                "parameter_name": parameter_name,
            }
        )
    )

    response = ssm_client.get_parameter(
        Name=parameter_name
    )

    environment = response["Parameter"]["Value"]

    logger.info(
        json.dumps(
            {
                "event": "ssm_get_parameter_completed",
                "parameter_name": parameter_name,
                "environment": environment,
            }
        )
    )

    return environment


def generate_helm_values(environment: str) -> dict:
    if environment not in ENVIRONMENT_HELM_CONFIG:
        logger.error(
            json.dumps(
                {
                    "event": "unsupported_environment",
                    "environment": environment,
                    "supported_environments": list(
                        ENVIRONMENT_HELM_CONFIG.keys()
                    ),
                }
            )
        )

        raise ValueError(
            f"Unsupported environment: {environment}"
        )

    replica_count = ENVIRONMENT_HELM_CONFIG[environment]["replica_count"]

    helm_values = {
        "replicaCount": str(replica_count)
    }

    logger.info(
        json.dumps(
            {
                "event": "helm_values_generated",
                "environment": environment,
                "controller_replica_count": replica_count,
                "helm_values": helm_values,
            }
        )
    )

    return helm_values


def on_event(event, context):
    request_type = event["RequestType"]

    logger.info(
        json.dumps(
            {
                "event": "custom_resource_invoked",
                "request_type": request_type,
                "request_id": getattr(context, "aws_request_id", None),
                "physical_resource_id": event.get("PhysicalResourceId"),
            }
        )
    )

    if request_type == "Delete":
        logger.info(
            json.dumps(
                {
                    "event": "custom_resource_delete",
                    "message": "Delete request received. No external cleanup required.",
                }
            )
        )

        return {
            "PhysicalResourceId": "HelmConfigResource"
        }

    parameter_name = os.environ["PARAMETER_NAME"]

    environment = get_environment(parameter_name)

    helm_values = generate_helm_values(environment)

    logger.info(
        json.dumps(
            {
                "event": "custom_resource_response",
                "environment": environment,
                "data": helm_values,
            }
        )
    )

    return {
        "PhysicalResourceId": "HelmConfigResource",
        "Data": helm_values,
    }