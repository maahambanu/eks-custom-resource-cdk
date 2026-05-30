#!/usr/bin/env python3
import aws_cdk as cdk

from eks_custom_resource_cdk.platform_stack import PlatformStack


app = cdk.App()

platform_config = app.node.try_get_context("platform")

if not platform_config:
    raise ValueError(
        "Missing 'platform' context in cdk.json. "
        "Check your cdk.json configuration."
    )

env_name = app.node.try_get_context("env") or "development"

valid_envs = list(platform_config["environments"].keys())

if env_name not in valid_envs:
    raise ValueError(
        f"Invalid environment '{env_name}'. "
        f"Must be one of: {valid_envs}"
    )

aws_env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "eu-west-1",
)

PlatformStack(
    app,
    f"SwisscomPlatformStack-{env_name.capitalize()}",
    env_name=env_name,
    platform_config=platform_config,
    env=aws_env,
    description=f"Swisscom iAWS Platform EKS Stack - {env_name}",
)

cdk.Tags.of(app).add("Project", platform_config["project_name"])
cdk.Tags.of(app).add("ManagedBy", "cdk")
cdk.Tags.of(app).add("Team", "platform-engineering")
cdk.Tags.of(app).add("Environment", env_name)
cdk.Tags.of(app).add("Owner", "maaham.banu")

app.synth()