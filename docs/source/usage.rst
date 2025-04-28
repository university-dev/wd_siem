Usage
=====

category: x

subject: Workday SIEM Integration - Product Description & Initial Deployment Guide

Workday SIEM Integration - Product Description & Initial Deployment Guide
-------------------------------------------------------------------------

**Product Description**
This process automates the fetching of activity logs from Workday and posts them to Azure for inspection by Microsoft Sentinel. The application is written in Python and built on AWS using the AWS CDK (Cloud Development Kit).

Each night at midnight, an AWS Lambda function is triggered by Amazon Eventbridge. The function collects activity logs from Workday for the past 24 hours using Workday's Privacy v1 /activityLogging endpoint. These logs are then sent to an Azure Log Analytics Workspace, where they can be inspected my Microsoft Sentinel.

[ ADD ] details about aws account where this is going to be deployed [ ADD ]

**AWS Cloud Development Kit & Bitbucket Pipelines**
The AWS CDK construct library provides APIs to define your CDK application and add CDK constructs to the application. It allows you to define and set up infrastructure as code, using familiar programming languages like Python.

Before deploying, make sure to have AWS CDK installed and configured properly. For a detailed getting started guide, follow steps outlined in [this repository](https://github.com/aws/aws-cdk?tab=readme-ov-file#getting-started) and for in depth information about concepts and specific resources see the [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/).

To make updates or fix issues, clone the repository using the provided installation source. Make sure CDK and your environment are set up, make the necessary changes, and commit them to the remote repository. This will automatically trigger a bitbucket-pipeline workflow to manage the deployment. The pipeline will take care of synthesizing and deploying your changes to the development environment. From there, the change will be reviewed and manually deployed into the production environment.

This app uses OpenID Connect (OIDC) to make sure only authorized users initiate and oversee pipeline execution. To set OIDC in your AWS environment, follow steps outlined in this [Atlassian article](https://support.atlassian.com/bitbucket-cloud/docs/deploy-on-aws-using-bitbucket-pipelines-openid-connect/).

Installation Source:    https://bitbucket.org/pointloma/wd_siem/src/main/


**Manual Configuration**
Pushing code to the remote repository will handle the majority of the required configurations, but a few specific values need to be manually set:

**AWS Secrets Manager**

The app generates these secrets during deployment. They are initializing with placeholder values that require updating. Find the secret names listed below in AWS Secrets Manager and update to their actual development or production values. You can find these credentials in Passwordstate.

Secret Names: workday_secret, sentinel_secret


**SNS Failure Notification Configuration**

The SNS failure topic is configured to send email notifications whenever the Lambda function fails to fetch or send messages. This ensures that the app's operator and any interested parties are informed of the failure and can take necessary manual intervention if required. To add email addresses for these notifications, locate the environment's JSON configuration (dev, staging, or prod) in the `cdk.json` file, find the `sns_failure_topic_email` field, and add the desired email addresses.
