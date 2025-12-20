# Deployment Setup Guide

This guide explains how to set up automated deployments to AWS EC2 using GitHub Actions and AWS Systems Manager (SSM).

## Overview

Deployments use AWS Systems Manager (SSM) instead of SSH for enhanced security:
- ✅ No SSH port exposure to GitHub Actions
- ✅ No IP allowlisting required
- ✅ AWS IAM-based authentication
- ✅ Command logging in CloudWatch

## Prerequisites

1. AWS account with appropriate permissions
2. GitHub repository with Actions enabled
3. Terraform installed locally

## Step 1: Apply Terraform Changes

The Terraform configuration has been updated to include SSM support. Apply the changes:

```bash
cd terraform
terraform init
terraform apply
```

This will create:
- IAM role with SSM permissions (`powers-land-ec2-ssm-role`)
- IAM instance profile attached to EC2 instance
- Outputs the EC2 instance ID needed for GitHub Actions

After applying, note the `instance_id` output:

```bash
terraform output instance_id
```

## Step 2: Create AWS IAM User for GitHub Actions

Create a dedicated IAM user for GitHub Actions deployments:

1. Go to AWS Console → IAM → Users → Create User
2. User name: `github-actions-powers-land`
3. Attach the following policy (create as inline policy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:SendCommand",
        "ssm:GetCommandInvocation"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:document/AWS-RunShellScript",
        "arn:aws:ssm:*:*:*"
      ]
    }
  ]
}
```

4. Create access keys for this user
5. Save the **Access Key ID** and **Secret Access Key** securely

## Step 3: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key ID | From Step 2 |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret access key | From Step 2 |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) | Your Terraform `aws_region` variable |
| `EC2_INSTANCE_ID` | EC2 instance ID | From `terraform output instance_id` |

### Old Secrets (Can Be Removed)

The following secrets are no longer needed and can be deleted:
- ~~`EC2_SSH_KEY`~~ (SSH no longer used)
- ~~`EC2_HOST`~~ (replaced by instance ID)

## Step 4: Verify SSM Agent

The SSM agent should already be running on Ubuntu 24.04 instances (installed via snap). To verify:

```bash
# SSH to your instance (still works from your allowed IP)
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip

# Check SSM agent status (Ubuntu 24.04 uses snap)
sudo snap services amazon-ssm-agent

# Should show: enabled  active

# If not installed, install it:
sudo snap install amazon-ssm-agent --classic
sudo snap start amazon-ssm-agent
```

Verify the instance is registered with Systems Manager (from your local machine):

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=YOUR_INSTANCE_ID" \
  --query 'InstanceInformationList[0].PingStatus' \
  --output text
```

Should return `Online` when ready (may take 5-10 minutes after first install).

## Step 5: Test Deployment

1. Push a commit to the `main` branch
2. Go to GitHub → Actions tab
3. Watch the deployment workflow run
4. The deployment will:
   - Run tests
   - Deploy via SSM (no SSH needed)
   - Verify the application is responding

## Deployment Process

When you push to `main`, GitHub Actions will:

1. **Test Stage**: Run pytest on all tests
2. **Deploy Stage** (via SSM):
   - Pull latest code from GitHub
   - Install/update Python dependencies
   - Run database migrations
   - Restart the application service
3. **Verify Stage**: Check that the site is responding

## Troubleshooting

### SSM Command Fails

Check the SSM agent status on EC2:
```bash
sudo systemctl status amazon-ssm-agent
sudo journalctl -u amazon-ssm-agent -n 50
```

### Permission Denied Errors

Verify the IAM instance profile is attached:
```bash
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

### View SSM Command Output

From AWS CLI:
```bash
aws ssm get-command-invocation \
  --command-id COMMAND_ID \
  --instance-id INSTANCE_ID \
  --output text
```

Or in AWS Console:
- Go to Systems Manager → Run Command
- View command history and output

## Security Benefits

Compared to SSH-based deployment:

| Feature | SSH | SSM |
|---------|-----|-----|
| Port exposure | Port 22 open to internet | No ports needed |
| Authentication | SSH keys | AWS IAM |
| IP restrictions | Requires allowlisting | Not needed |
| Audit logging | SSH logs only | CloudWatch + CloudTrail |
| Key management | Manual key rotation | AWS managed |

## Manual Deployment (if needed)

You can still SSH to the instance from your allowed IP for manual operations:

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip
cd /var/www/powers-land
sudo -u powers-land git pull origin main
sudo -u powers-land bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u powers-land bash -c "source venv/bin/activate && FLASK_APP=wsgi.py flask db upgrade"
sudo systemctl restart powers-land
```

## Next Steps

- Consider enabling CloudWatch logging for the application
- Set up CloudWatch alarms for deployment failures
- Add Slack/email notifications for deployment status
