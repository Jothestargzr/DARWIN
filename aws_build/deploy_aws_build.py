import subprocess
import time
import json
import os

# deploy_aws_build.py
# Orchestrates the execution of the AWS build.

SSH_KEY_PATH = "~/.ssh/darwin-aws-key.pem"
REMOTE_USER = "ec2-user" # Or 'mac' depending on the AMI

def run_local(command):
    print(f"Running local: {command}")
    subprocess.run(command, shell=True, check=True)

def run_remote(ip, command):
    print(f"Running remote on {ip}: {command}")
    ssh_cmd = f"ssh -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {REMOTE_USER}@{ip} '{command}'"
    subprocess.run(ssh_cmd, shell=True, check=True)

def scp_to_remote(ip, local_path, remote_path):
    print(f"Copying {local_path} to {ip}:{remote_path}")
    scp_cmd = f"scp -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {local_path} {REMOTE_USER}@{ip}:{remote_path}"
    subprocess.run(scp_cmd, shell=True, check=True)

def scp_from_remote(ip, remote_path, local_path):
    print(f"Downloading {remote_path} from {ip} to {local_path}")
    scp_cmd = f"scp -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {REMOTE_USER}@{ip}:{remote_path} {local_path}"
    subprocess.run(scp_cmd, shell=True, check=True)

def main():
    print("--- DARWIN OS AWS ORCHESTRATOR ---")
    
    # 1. Provision Infrastructure
    print("1. Provisioning AWS Mac EC2 Instance...")
    run_local("bash aws_darwin_builder.sh")
    
    # Read output
    with open("aws_provision_data.json", "r") as f:
        data = json.load(f)
    
    public_ip = data['public_ip']
    
    # Wait for SSH to become available
    print("Waiting 60 seconds for macOS to fully boot SSH daemon...")
    time.sleep(60)

    # 2. Upload and Execute Build Script
    print("2. Uploading build script...")
    scp_to_remote(public_ip, "remote_build.sh", "~/remote_build.sh")
    
    print("3. Executing Build Pipeline on EC2...")
    # Make executable and run (this streams stdout back locally)
    run_remote(public_ip, "chmod +x ~/remote_build.sh && bash ~/remote_build.sh")
    
    # 4. Download Artifacts
    print("4. Downloading compiled DMG...")
    scp_from_remote(public_ip, "/tmp/chromium/**/*.dmg", "./")
    
    print("✅ AWS Build Pipeline Finished Successfully!")
    print("WARNING: Remember to release your AWS Dedicated Host after 24 hours to avoid continuous billing!")

if __name__ == "__main__":
    main()
