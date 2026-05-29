import aws_cdk as core
import aws_cdk.assertions as assertions

from eks_custom_resource_cdk.eks_custom_resource_cdk_stack import EksCustomResourceCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in eks_custom_resource_cdk/eks_custom_resource_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EksCustomResourceCdkStack(app, "eks-custom-resource-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
