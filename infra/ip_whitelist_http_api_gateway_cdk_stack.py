from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_apigatewayv2_alpha as _apigwv2,
    aws_apigatewayv2_integrations_alpha as _apigwv2_integ,
    aws_apigatewayv2_authorizers_alpha as _apigwv2_auth,
    aws_lambda as _lambda,
    aws_cloudfront as _cloudfront,
    aws_cloudfront_origins as _origins,
    aws_iam as _iam,
    aws_waf as _waf,
)
from constructs import Construct
import os
from .ip_whitelist import IP_WHITE_LIST

IDENTITY_SOURCE_HEADER = 'X-Cfn-Header'

class IpWhitelistHttpApiGatewayCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._account_id = os.environ['CDK_DEFAULT_ACCOUNT']
        self._region = os.environ['CDK_DEFAULT_REGION']


        # Create Lambda function
        self._fn_hello = self._create_lambda_hello()

        # Create Lambda Auth for Cloudfront
        self._fn_cf_auth = self._create_lambda_cf_auth()

        # Create HTTP API Gateway
        self._http_api = _apigwv2.HttpApi(self, 'HelloApi')
        
        # Create Lambda Integration
        self._hello_lambda_integ = _apigwv2_integ.HttpLambdaIntegration(
            'HelloLambdaIntegration', self._fn_hello
        )

        # Create Lambda authorizer
        self._cfn_lambda_auth = _apigwv2_auth.HttpLambdaAuthorizer(
            'CloudfrontAuthorizer',self._fn_cf_auth,
            response_types=[_apigwv2_auth.HttpLambdaResponseType.SIMPLE],
            identity_source = [f'$request.header.{IDENTITY_SOURCE_HEADER}']
        )

        # Create route
        self._http_api.add_routes(
            path='/hello',
            methods=[_apigwv2.HttpMethod.GET],
            integration=self._hello_lambda_integ,
            authorizer=self._cfn_lambda_auth
        )

        # Create Whitelist IP Set
        self._waf_whitelist_ip_set = _waf.CfnIPSet(
            self,
            'WhilteListIpSet',
            name=f'{self._http_api.api_id}-whitelist',
            ip_set_descriptors=IP_WHITE_LIST
        )

        # Create WAF Rule
        self._waf_rule = _waf.CfnRule(
            self,
            'WhilteListWafRule',
            name=f'{self._http_api.api_id}IpWhiteListRule',
            metric_name=f'{self._http_api.api_id}IpWhiteListRule',
            predicates=[
                _waf.CfnRule.PredicateProperty(
                    data_id=self._waf_whitelist_ip_set.ref,
                    negated=False,
                    type='IPMatch'
            )]
        )

        # Create WAF WebAcl
        self._waf_webacl = _waf.CfnWebACL(
            self,
            'WhilteListWebAcl',
            name=f'{self._http_api.api_id}WhilteListWebAcl',
            metric_name=f'{self._http_api.api_id}WhilteListWebAcl',
            default_action=_waf.CfnWebACL.WafActionProperty(
                type='BLOCK'
            ),
            rules=[
                _waf.CfnWebACL.ActivatedRuleProperty(
                    priority=100,
                    rule_id=self._waf_rule.ref,
                    action=_waf.CfnWebACL.WafActionProperty(
                        type='ALLOW'
                    )
                )
            ]
        )

        # Create secret value
        self._secret_value = f'{self._http_api.api_id}-{self._region}'

        # Add value to auth lamnbda env variable
        self._fn_cf_auth.add_environment(
            key='secret',
            value=self._secret_value
        )

        # Create Cloudfront distribution
        self._dist = _cloudfront.Distribution(
            self,
            'EdgeHttpApiGw',
            default_behavior=_cloudfront.BehaviorOptions(
                origin=_origins.HttpOrigin(
                    f'{self._http_api.api_id}.execute-api.{self._region}.amazonaws.com',
                    custom_headers=
                        {IDENTITY_SOURCE_HEADER: self._secret_value}
                )
            ),
            web_acl_id=self._waf_webacl.ref
        )

        CfnOutput(
            self,
            'HTTP API EndPoint',
            description='HTTP API Endpoint',
            value=f'{self._http_api.api_endpoint}/hello'
        )

        CfnOutput(
            self,
            'Cloudfront Distribution Domain Nanme',
            description='Cloudfront Distribution Domain Nanme',
            value=f'https://{self._dist.domain_name}/hello'
        )

        CfnOutput(
            self,
            'Lambda Auth Function Arn',
            description='Lambda Auth Function Arn',
            value=self._fn_cf_auth.function_arn
        )

        CfnOutput(
            self,
            'Lambda Hello Function Arn',
            description='Lambda Hello Function Arn',
            value=self._fn_hello.function_arn
        )
        
    def _create_lambda_hello(self):
        return _lambda.Function(
            self, 'LambdaHello',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='app.handler',
            code=_lambda.Code.from_asset(
                path='src/hello'
            ),
            timeout=Duration.minutes(1),
            memory_size=128,
            environment={
                'REGION': self._region,
                'ACCOUNT_ID': self._account_id
            },
        )
    
    def _create_lambda_cf_auth(self):
        return _lambda.Function(
            self, 'LambdaCfAuth',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='app.handler',
            code=_lambda.Code.from_asset(
                path='src/cfAuth'
            ),
            timeout=Duration.minutes(1),
            memory_size=128,
            environment={
                'REGION': self._region,
                'ACCOUNT_ID': self._account_id
            },
        )
    
    def _create_waf(self):
        pass

    def _create_cloudfront(self):
        pass
