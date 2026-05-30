from pathlib import Path

from aws_cdk import (
    CfnOutput,
    CustomResource,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_ssm as ssm,
    custom_resources as cr,
)
from aws_cdk.lambda_layer_kubectl_v30 import KubectlV30Layer
from constructs import Construct


LOG_RETENTION_MAPPING = {
    3: logs.RetentionDays.THREE_DAYS,
    7: logs.RetentionDays.ONE_WEEK,
    30: logs.RetentionDays.ONE_MONTH,
}

KUBERNETES_VERSION_MAPPING = {
    "1.30": eks.KubernetesVersion.V1_30,
}


class PlatformStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        platform_config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environment_config = platform_config["environments"][env_name]
        eks_config = platform_config["eks"]
        ingress_config = platform_config["ingress_nginx"]

        project_name = platform_config["project_name"]
        parameter_name = platform_config["ssm_parameter_name"]

        env_parameter = ssm.StringParameter(
            self,
            "AccountEnvironmentParameter",
            parameter_name=parameter_name,
            string_value=env_name,
            description="Platform account environment",
        )

        vpc = ec2.Vpc(
            self,
            "PlatformVpc",
            max_azs=platform_config["vpc"]["max_azs"],
            nat_gateways=platform_config["vpc"]["nat_gateways"],
        )

        kubectl_layer = KubectlV30Layer(
            self,
            "KubectlLayer",
        )

        cluster = eks.Cluster(
            self,
            "PlatformEksCluster",
            cluster_name=f"{project_name}-{env_name}",
            version=KUBERNETES_VERSION_MAPPING[eks_config["version"]],
            kubectl_layer=kubectl_layer,
            vpc=vpc,
            default_capacity=0,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
        )

        node_group = cluster.add_nodegroup_capacity(
            "PlatformManagedNodeGroup",
            desired_size=environment_config["node_count"],
            min_size=platform_config["node_group"]["min_size"],
            max_size=platform_config["node_group"]["max_size"],
            instance_types=[
                ec2.InstanceType(eks_config["instance_type"])
            ],
            disk_size=eks_config["disk_size"],
        )

        lambda_path = Path(__file__).resolve().parent.parent / "lambda"

        helm_config_function = lambda_.Function(
            self,
            "HelmConfigFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler=platform_config["lambda"]["handler"],
            code=lambda_.Code.from_asset(str(lambda_path)),
            timeout=Duration.seconds(
                platform_config["lambda"]["timeout_seconds"]
            ),
            memory_size=platform_config["lambda"]["memory_size"],
            log_retention=LOG_RETENTION_MAPPING[
                environment_config["log_retention_days"]
            ],
            environment={
                "PARAMETER_NAME": parameter_name,
                "LOG_LEVEL": platform_config["lambda"]["log_level"],
                "ENVIRONMENT": env_name,
            },
        )

        env_parameter.grant_read(helm_config_function)

        provider = cr.Provider(
            self,
            "HelmConfigProvider",
            on_event_handler=helm_config_function,
            log_retention=LOG_RETENTION_MAPPING[
                environment_config["log_retention_days"]
            ],
        )

        helm_config_resource = CustomResource(
            self,
            "HelmConfigCustomResource",
            service_token=provider.service_token,
        )

        helm_config_resource.node.add_dependency(env_parameter)

        ingress_chart = cluster.add_helm_chart(
            "IngressNginx",
            repository=ingress_config["repository"],
            chart=ingress_config["chart"],
            version=ingress_config["version"],
            release=ingress_config["release"],
            namespace=ingress_config["namespace"],
            create_namespace=True,
            wait=False,
            timeout=Duration.minutes(15),
            values={
                "controller": {
                    "replicaCount": helm_config_resource.get_att_string(
                        "replicaCount"
                    ),
                    "service": {
                        "type": ingress_config["service_type"]
                    },
                    "admissionWebhooks": {
                        "enabled": ingress_config["admission_webhooks_enabled"]
                    },
                    "resources": {
                        "requests": {
                            "cpu": ingress_config["resources"]["requests"]["cpu"],
                            "memory": ingress_config["resources"]["requests"]["memory"],
                        },
                        "limits": {
                            "cpu": ingress_config["resources"]["limits"]["cpu"],
                            "memory": ingress_config["resources"]["limits"]["memory"],
                        },
                    },
                }
            },
        )

        ingress_chart.node.add_dependency(node_group)
        ingress_chart.node.add_dependency(helm_config_resource)

        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ClusterArn", value=cluster.cluster_arn)

        CfnOutput(
            self,
            "EnvironmentParameterName",
            value=env_parameter.parameter_name,
        )

        CfnOutput(self, "Environment", value=env_name)

        CfnOutput(
            self,
            "HelmConfigFunctionArn",
            value=helm_config_function.function_arn,
        )