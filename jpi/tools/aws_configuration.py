#!/usr/bin/env python

import logging
import os
import sys

import boto3

from jpi import settings


ROLE_NAME = 'jpi-cfn-role'
POLICY_ARNS = (
    "arn:aws:iam::aws:policy/AWSLambdaFullAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess",
    "arn:aws:iam::aws:policy/service-role/AWSConfigRole",
    "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator",
    "arn:aws:iam::aws:policy/AmazonCognitoPowerUser",
    "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess",
)
logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format=settings.LOGGING_FORMAT
)
logger = logging.getLogger()


def create_role():
    policy_path = os.path.join(
        settings.PROJECT_PATH, 'etc', 'jpi-cfn-role-trust-policy.json'
    )
    with open(policy_path) as f:
        return iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=f.read()
        )


if __name__ == "__main__":
    iam = boto3.client('iam')
    try:
        role = iam.get_role(RoleName=ROLE_NAME)
    except iam.exceptions.NoSuchEntityException:
        role = create_role()
        arn = role["Role"]["Arn"]
        logger.info(f'Role "{ROLE_NAME}" created. Its ARN: {arn}')
    else:
        arn = role["Role"]["Arn"]
        logger.info(f'Role "{ROLE_NAME}" already exists. Its ARN: {arn}')
    logger.info(f'Attaching role policies...')
    for policy in POLICY_ARNS:
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy)
        logger.info(f'Role policy "{policy}" attached to the role')
