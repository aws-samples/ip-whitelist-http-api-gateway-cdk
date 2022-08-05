import aws_cdk as core
import aws_cdk.assertions as assertions

from ip_whitelist_http_api_gateway_cdk.ip_whitelist_http_api_gateway_cdk_stack import IpWhitelistHttpApiGatewayCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ip_whitelist_http_api_gateway_cdk/ip_whitelist_http_api_gateway_cdk_stack.py
def test_http_api_created():
    app = core.App()
    stack = IpWhitelistHttpApiGatewayCdkStack(app, 'ip-whitelist-http-api-gateway-cdk')
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        'AWS::ApiGatewayV2::Api', 
        {
            'ProtocolType': 'HTTP'
        }
    )
