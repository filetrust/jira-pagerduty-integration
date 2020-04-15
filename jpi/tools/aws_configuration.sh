#!/bin/bash

ROLE_NAME=jpi-cfn-role

ROLE=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://etc/jpi-cfn-role-trust-policy.json)
EXIT_STATUS=$?
if [ "$EXIT_STATUS" -eq 0 ]; then
    echo "Role \"$ROLE_NAME\" created."
else
    ROLE=$(aws iam get-role --role-name $ROLE_NAME)
fi
echo "$ROLE" | jq .Role.Arn | while read ARN; do echo "ARN of the role \"$ROLE_NAME\": $ARN"; done

POLICY_ARNS=(
    "arn:aws:iam::aws:policy/AWSLambdaFullAccess"
    "arn:aws:iam::aws:policy/IAMFullAccess"
    "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
    "arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator"
    "arn:aws:iam::aws:policy/AmazonCognitoPowerUser"
    "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess"
)
for POLICY_ARN in "${POLICY_ARNS[@]}"
do
    aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $POLICY_ARN
    echo "Role policy \"$POLICY_ARN\" attached to the role"
done
