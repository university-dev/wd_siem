import os

from constructs import Construct
from aws_cdk import (
    Duration,
    SecretValue,
    aws_sns as sns,
    aws_secretsmanager as sm,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_iam as iam,
    aws_sns_subscriptions as sns_sub,
    aws_s3_notifications as s3_notifications,
    CfnOutput
)

from cdk_utils.cdk_utils import PLNULambda, PLNUStack

BASE_PATH = os.path.join(os.path.dirname(__file__), "..")
REL_SRC_PATH = os.path.join("src")
SRC_PATH = os.path.join(BASE_PATH, REL_SRC_PATH)
LAYER_PATH = os.path.join(BASE_PATH, "lambda-layer", "python.zip")


class WdSiemStack(PLNUStack):
    """
    WdSiemStack automates the process of fetching activity logs from Workday and posting them to Azure for inspection using Microsoft Sentinel.
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environment = self.cdk_env.get('environment')

        # Create SNS failure topic for Lambda failures and subscribe email addresses to receive notifications.
        sns_fail_queue = sns.Topic(self, 'WorkdayLogsLambdaFailure')
        for email in self.cdk_env.get('sns_failure_topic_email').split(','):
            sns_fail_queue.add_subscription(sns_sub.EmailSubscription(email))

        # IAM user for Workday EIB
        wd_eib_user = iam.User(self, 'workday_iam', user_name='wd_eib_user')
        access_key = iam.CfnAccessKey(self, "WorkdayAccessKey", user_name=wd_eib_user.user_name)

        bucket_name = 'workday-activity-logs'
        if environment == 'dev':
            bucket_name = 'workday-activity-logs-dev'

        bucket = s3.Bucket(self, bucket_name, block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                           bucket_name=bucket_name, encryption=s3.BucketEncryption.S3_MANAGED,
                           enforce_ssl=True, lifecycle_rules=[s3.LifecycleRule(id="DeleteAfterOneWeek", expiration=Duration.days(7))])

        bucket.grant_put(wd_eib_user)

        # Set up basic environment variables for Lambda function
        default_env = {'deploy_environment': environment,
                       'log_level': self.cdk_env.get('log_level'),
                       'sns_fail_queue': sns_fail_queue.topic_arn,
                       'account_number': self.cdk_env.get('account'),
                       'environment': environment
                       }

        azure_identity_layer = _lambda.LayerVersion(
            self,
            "azure_identity_layer",
            description="A layer containing Azure SDK dependencies",
            layer_version_name="azure_identity_layer",
            code=_lambda.Code.from_asset(LAYER_PATH),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        )

        lambda_factory = PLNULambda(default_env=default_env)

        fetch_and_send_workday_logs = \
            lambda_factory.basic_lambda(self, "fetch_and_send_workday_logs", SRC_PATH, BASE_PATH, REL_SRC_PATH, 30,
                                        "Processes Workday logs from S3 and sends to Azure Sentinel.", 256, 2, layers=[azure_identity_layer])

        notification = s3_notifications.LambdaDestination(fetch_and_send_workday_logs)
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification)
        bucket.grant_read_write(fetch_and_send_workday_logs)

        sentinel_secret = sm.Secret(
            self,
            "sentinel_secret",
            secret_name="sentinel_secret",
            secret_object_value={
                "dce_endpoint": SecretValue.unsafe_plain_text("<change_me>"),
                "dcr_immutable_id": SecretValue.unsafe_plain_text("<change_me>"),
                "dcr_stream_name": SecretValue.unsafe_plain_text("<change_me>"),
                "client_id": SecretValue.unsafe_plain_text("<change_me>"),
                "client_secret": SecretValue.unsafe_plain_text("<change_me>"),
                "scopes_aka_tenant_id": SecretValue.unsafe_plain_text("<change_me>")
            },
            description="Azure/Sentinel API Credentials JSON",
        )

        sentinel_secret.grant_read(fetch_and_send_workday_logs)
        sns_fail_queue.grant_publish(fetch_and_send_workday_logs)
