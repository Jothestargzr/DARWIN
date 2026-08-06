#!/bin/bash
set -e

# aws_darwin_builder.sh
# Automates the creation of an AWS EC2 Mac Dedicated Host and Instance for DARWIN OS compilation.

INSTANCE_TYPE="mac2.metal" # M2 Pro Mac
REGION="us-east-1"
AZ="us-east-1a"
AMI_ID="ami-0d2207b7dbd791522" # Standard macOS Sonoma AMI (update if needed)
KEY_NAME="darwin-aws-key"

echo "🚀 Starting AWS EC2 Mac provisioning sequence..."

# 1. Allocate Dedicated Host
echo "[1/4] Allocating Dedicated Host ($INSTANCE_TYPE)..."
HOST_ID=$(aws ec2 allocate-hosts \
    --instance-type $INSTANCE_TYPE \
    --availability-zone $AZ \
    --auto-placement "on" \
    --quantity 1 \
    --region $REGION \
    --query 'HostIds[0]' \
    --output text)

if [ -z "$HOST_ID" ]; then
    echo "❌ Failed to allocate Dedicated Host."
    exit 1
fi
echo "✅ Host allocated: $HOST_ID"

# 2. Wait for Host to be available
echo "[2/4] Waiting for Host to become available (can take a few minutes)..."
aws ec2 wait host-available --host-ids $HOST_ID --region $REGION
echo "✅ Host is available!"

# 3. Launch EC2 Instance on the Host
echo "[3/4] Launching macOS Instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --placement "Tenancy=host,HostId=$HOST_ID" \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# 4. Wait for Instance and get IP
echo "[4/4] Waiting for Instance to run and get public IP..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🎉 EC2 Mac Instance successfully provisioned!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Host ID: $HOST_ID"

# Output JSON for orchestrator script
echo "{\"instance_id\": \"$INSTANCE_ID\", \"public_ip\": \"$PUBLIC_IP\", \"host_id\": \"$HOST_ID\"}" > aws_provision_data.json
