import json
import os
import boto3
import logging

from botocore.exceptions import ClientError
from azure.identity import ClientSecretCredential
from azure.monitor.ingestion import LogsIngestionClient
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError

s3 = boto3.client('s3')
sm = boto3.client('secretsmanager')

log_level = os.getenv('log_level', 'INFO')
sns_failure_arn = os.getenv('sns_fail_queue')
account_number = os.getenv('account_number')
environment = os.getenv('environment')

log_lvl_num = getattr(logging, log_level, None)
if log_lvl_num is None:
    log_lvl_num = getattr(logging, 'INFO')
logger = logging.getLogger()
logger.setLevel(log_lvl_num)


def send_sns_message(error, topic_arn, acct_number, env):
    sns = boto3.client('sns')
    subject = f"[ {env} ] Error in Automated Workday Logs Process - AWS Account: {acct_number}"
    message = (
        """An error occurred in the automated process responsible for collecting and sending Workday logs to Azure.
        \n\n\nAWS Account: {account}\nLambda Function: fetch_and_send_workday_logs\nError Details: {error_details}\n"""
    )
    formatted_message = message.format(account=acct_number, error_details=str(error))
    try:
        response = sns.publish(TopicArn=topic_arn, Message=formatted_message, Subject=subject)
        logger.info(f"Message sent to SNS topic {topic_arn}: {response['MessageId']}")
    except ClientError as e:
        logger.error(f"Failed to send message to SNS topic {topic_arn}: {str(e)}")
        raise


class AzureLogAnalyticsClient:
    def __init__(self, endpoint: str, rule_id_aka_immutable_id: str, dcr_stream_name: str, scopes_aka_tenant_id: str,
                 client_id: str, client_secret: str):
        """
        Creates an Azure service object using the provided API client credentials.

        :param endpoint: The endopoint URL for the Log Analytics workspace.
        :param rule_id: The data collection rule ID.
        :param stream_name: The name of the data stream.
        :param tenant_id: The Azure Active Directory tenant ID.
        :param client_id: The client secret of the Azure Active Directory application.
        :param client_secret: The client secret of the Azure Active Directory application.
        """
        self.endpoint = endpoint
        self.rule_id = rule_id_aka_immutable_id
        self.stream_name = dcr_stream_name
        self.tenant_id = scopes_aka_tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.credential = ClientSecretCredential(tenant_id=self.tenant_id, client_id=self.client_id,
                                                 client_secret=self.client_secret)
        self.client = LogsIngestionClient(endpoint=self.endpoint, credential=self.credential, logging_enable=True)

    def send_logs(self, data):
        """
        Uploads a list of log entries to Azure Log Analytics.

        :param data: The Workday logs to be sent.
        :return: The result of th elog upload operation.
        """
        try:
            result = self.client.upload(rule_id=self.rule_id, stream_name=self.stream_name, logs=data)
            logger.info(result)
            return result
        except (ClientAuthenticationError, HttpResponseError, Exception) as error:
            logger.error(f"Log upload failed due to: {str(error)}")
            raise


def lambda_handler(event, context):
    """
    Retrieve and format data from S3 and send logs to Azure Log Analytics Workspace.

    :param event: The event data passed to the Lambda function.
    :param context: The Lambda execution context.
    """

    try:
        sentinel_secrets = json.loads(sm.get_secret_value(SecretId="sentinel_secret").get('SecretString'))

        bucket_name = event.get('Records')[0]['s3']['bucket']['name']
        object_key = event.get('Records')[0]['s3']['object']['key']

        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        user_activity_logs = json.loads(response['Body'].read().decode('utf-8')).get('Report_Entry', [])

        sentinel = AzureLogAnalyticsClient(
            sentinel_secrets.get('dce_endpoint'),
            sentinel_secrets.get('dcr_immutable_id'),
            sentinel_secrets.get('dcr_stream_name'),
            sentinel_secrets.get('scopes_aka_tenant_id'),
            sentinel_secrets.get('client_id'),
            sentinel_secrets.get('client_secret')
        )

        sentinel.send_logs(user_activity_logs)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        send_sns_message(str(e), sns_failure_arn, account_number, environment)
