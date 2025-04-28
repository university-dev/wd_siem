#!/bin/bash

read -p "Enter AWS profile: " profile

read -p "Do you want to perform initial set up or reset? (initial setup/reset): " action

if [[ "$action" == "initial setup" || "$action" == i* ]]; then
  echo "Performing initial setup.."

  aws cloudformation set-stack-policy --stack-name wd-siem --stack-policy-body file://policies/wd_siem_stack_policy.json --profile $profile --region us-west-2
echo "Initial setup complete."
elif [[ "$action" ==  "reset" || "$action" == r* ]]; then
  echo "Performing reset..."

  aws cloudformation set-stack-policy --stack-name wd-siem --stack-policy-body file://policies/reset.json --profile $profile --region us-west-2
  echo "..."
  sleep 1
  echo "Reset complete."
else
  echo "Invalid option. Please choose 'initial setup' or 'reset'."
fi
