# Mise Task Runner Reference

This document provides complete reference documentation for all mise tasks defined in `.mise.toml`.

## What is Mise?

[Mise](https://mise.jdx.dev/) is an optional task runner that provides shorter command aliases for Bruno CLI requests. **All mise tasks are wrappers around `bru run` commands** - they execute the same `.bru` files with the same authentication flow.

**Key Point**: You don't need mise. Every `mise run` command shown below can be replaced with its `bru run` equivalent (shown in each section).

## Installation

```bash
# Install mise (optional)
curl https://mise.run | sh

# Verify installation
mise --version

# View all available tasks
mise tasks
```

## Command Equivalence

Every mise task is a shorthand for a `bru run` command. Here's the pattern:

```bash
# Mise command
mise run vpc:list

# Equivalent bru command
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

Mise simply:
1. Runs authentication first (`auth/get-iam-token.bru`)
2. Runs your request (e.g., `vpc/list-vpcs.bru`)
3. Uses `--env prod` by default
4. Passes through any environment variables you set

## Task Reference

All tasks below show both the mise command and its bru equivalent.

### Authentication

```bash
# Mise
mise run auth

# Bru equivalent
bru run auth/get-iam-token.bru --env prod
```

**Description**: Get IBM Cloud IAM token
**Environment Variables**: Requires `IBM_API_KEY`
**Output**: Token expiration time and validity
**Token Lifetime**: 1 hour

### Resource Groups

#### List Resource Groups
```bash
# Mise
mise run resource-groups:list

# Bru equivalent
bru run auth/get-iam-token.bru resource-groups/list-resource-groups.bru --env prod
```

**Description**: List all resource groups in your account
**Output**: Resource group IDs, names, account IDs, states

#### Get Resource Group by Name
```bash
# Mise
RESOURCE_GROUP_NAME="Default" mise run resource-groups:get-by-name

# Bru equivalent
RESOURCE_GROUP_NAME="Default" bru run auth/get-iam-token.bru resource-groups/get-resource-group-by-name.bru --env prod
```

**Description**: Find resource group ID by name
**Required**: `RESOURCE_GROUP_NAME`
**Output**: Resource group ID
**Use Case**: Get ID for VPC/subnet creation

### VPC Operations

#### List VPCs
```bash
# Mise
mise run vpc:list

# Bru equivalent
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

**Description**: List all VPCs
**Output**: VPC names, IDs, statuses, regions, creation dates

#### List VPCs (Paginated)
```bash
# Mise - First page
mise run vpc:list-paginated

# Bru equivalent - First page
bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod

# Mise - Custom limit
PAGINATION_LIMIT=10 mise run vpc:list-paginated

# Bru equivalent - Custom limit
PAGINATION_LIMIT=10 bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod

# Mise - Next page
START_TOKEN="abc123..." PAGINATION_LIMIT=10 mise run vpc:list-paginated

# Bru equivalent - Next page
START_TOKEN="abc123..." PAGINATION_LIMIT=10 bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod
```

**Description**: List VPCs with cursor-based pagination
**Optional**: `PAGINATION_LIMIT` (1-100), `START_TOKEN`
**Output**: VPCs, pagination info, next token
**Use Case**: Accounts with >50 VPCs

#### Get Specific VPC
```bash
# Mise
VPC_ID=r006-abc123... mise run vpc:get

# Bru equivalent
VPC_ID=r006-abc123... bru run auth/get-iam-token.bru vpc/get-vpc.bru --env prod
```

**Description**: Get specific VPC details
**Required**: `VPC_ID`
**Output**: VPC details, default resources, CSE IPs

#### Create VPC
```bash
# Mise
NEW_VPC_NAME="my-vpc" RESOURCE_GROUP_ID="xyz..." mise run vpc:create

# Bru equivalent
NEW_VPC_NAME="my-vpc" RESOURCE_GROUP_ID="xyz..." bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod
```

**Description**: Create new VPC
**Required**: `NEW_VPC_NAME`
**Optional**: `RESOURCE_GROUP_ID`
**Output**: VPC ID, default security group, network ACL, routing table

### Subnet Operations

#### List Subnets
```bash
mise run subnets:list
```

**Description**: List all subnets
**Output**: Subnet names, IDs, CIDRs, zones, available IPs

#### Get Specific Subnet
```bash
SUBNET_ID=r006-def456... mise run subnets:get
```

**Description**: Get specific subnet details
**Required**: `SUBNET_ID`
**Output**: Subnet details, reserved IPs categorized by type

#### Create Subnet (IP Count)
```bash
NEW_SUBNET_NAME="my-subnet" VPC_ID=r006-abc ZONE_NAME=us-south-1 SUBNET_IP_COUNT=256 mise run subnets:create
```

**Description**: Create subnet with IP count (auto-assign CIDR)
**Required**: `NEW_SUBNET_NAME`, `VPC_ID`, `ZONE_NAME`, `SUBNET_IP_COUNT`
**Valid IP Counts**: 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192 (powers of 2)
**Recommended**: Use this method (simpler than CIDR)

#### Create Subnet (CIDR)
```bash
NEW_SUBNET_NAME="my-subnet" VPC_ID=r006-abc ZONE_NAME=us-south-1 SUBNET_CIDR=10.240.0.0/24 mise run subnets:create-by-cidr
```

**Description**: Create subnet with specific CIDR block
**Required**: `NEW_SUBNET_NAME`, `VPC_ID`, `ZONE_NAME`, `SUBNET_CIDR`
**Use Case**: When you need exact IP range control

### Security Group Operations

#### List Security Groups
```bash
mise run security-groups:list
```

**Description**: List all security groups
**Output**: Security group names, IDs, VPC associations

#### Get Specific Security Group
```bash
SECURITY_GROUP_ID=r006-ghi789... mise run security-groups:get
```

**Description**: Get security group with all rules
**Required**: `SECURITY_GROUP_ID`
**Output**: Group details, all rules with direction, protocol, ports, remote

#### Create Security Group
```bash
NEW_SG_NAME="web-servers" VPC_ID=r006-abc mise run security-groups:create
```

**Description**: Create empty security group
**Required**: `NEW_SG_NAME`, `VPC_ID`
**Output**: Security group ID
**Next Steps**: Add rules using security-groups:add-* tasks

#### Add Self-Reference Rule
```bash
SECURITY_GROUP_ID=r006-ghi mise run security-groups:add-self
```

**Description**: Allow inbound traffic from same security group
**Required**: `SECURITY_GROUP_ID`
**Use Case**: Allow instances in group to communicate

#### Add Outbound All Rule
```bash
SECURITY_GROUP_ID=r006-ghi mise run security-groups:add-outbound
```

**Description**: Allow all outbound traffic
**Required**: `SECURITY_GROUP_ID`
**Use Case**: Allow instances to reach internet for updates

#### Add SSH Rule
```bash
# Allow SSH from anywhere (not recommended for production)
SECURITY_GROUP_ID=r006-ghi mise run security-groups:add-ssh

# Allow SSH from specific IP/CIDR (recommended)
SECURITY_GROUP_ID=r006-ghi SSH_SOURCE_CIDR="203.0.113.0/24" mise run security-groups:add-ssh
```

**Description**: Allow SSH inbound (port 22)
**Required**: `SECURITY_GROUP_ID`
**Optional**: `SSH_SOURCE_CIDR` (default: 0.0.0.0/0)
**Security**: Always restrict to known IPs in production

#### Add HTTP Rule
```bash
SECURITY_GROUP_ID=r006-ghi mise run security-groups:add-http
```

**Description**: Allow HTTP inbound (port 80)
**Required**: `SECURITY_GROUP_ID`
**Use Case**: Web servers

#### Add HTTPS Rule
```bash
SECURITY_GROUP_ID=r006-ghi mise run security-groups:add-https
```

**Description**: Allow HTTPS inbound (port 443)
**Required**: `SECURITY_GROUP_ID`
**Use Case**: Secure web servers

#### Add Custom Rule
```bash
SECURITY_GROUP_ID=r006-ghi RULE_DIRECTION=inbound RULE_PROTOCOL=tcp PORT_MIN=8080 PORT_MAX=8080 REMOTE_CIDR=10.0.0.0/8 mise run security-groups:add-rule
```

**Description**: Add custom security group rule
**Required**: `SECURITY_GROUP_ID`, `RULE_DIRECTION`, `RULE_PROTOCOL`
**Optional**: `REMOTE_CIDR`, `REMOTE_SG_ID`, `PORT_MIN`, `PORT_MAX`, `ICMP_TYPE`, `ICMP_CODE`
**Protocols**: tcp, udp, icmp, all
**Directions**: inbound, outbound

### Instance Operations

#### List Instances
```bash
mise run instances:list
```

**Description**: List all virtual server instances
**Output**: Instance names, IDs, profiles, zones, VPCs, IPs, statuses

#### Get Specific Instance
```bash
INSTANCE_ID=r006-jkl012... mise run instances:get
```

**Description**: Get instance details
**Required**: `INSTANCE_ID`
**Output**: Compute config, OS, network interfaces, volumes, IPs

#### List Instance Profiles
```bash
mise run instances:list-profiles
```

**Description**: List all instance profiles (compute configurations)
**Output**: Profile names, vCPUs, memory, bandwidth, families
**Profiles**: bx2 (balanced), cx2 (compute), mx2 (memory), etc.

#### List Images
```bash
mise run instances:list-images
```

**Description**: List all available OS images
**Output**: Image IDs, names, OS details, architectures
**Images**: Ubuntu, RHEL, Debian, Windows Server, etc.

#### Create Instance
```bash
NEW_INSTANCE_NAME="web-01" VPC_ID=r006-abc ZONE_NAME=us-south-1 PROFILE_NAME=cx2-2x4 IMAGE_ID=r006-img SUBNET_ID=r006-sub SECURITY_GROUP_ID=r006-sg SSH_KEY_ID=r006-key mise run instances:create
```

**Description**: Create virtual server instance
**Required**: `NEW_INSTANCE_NAME`, `VPC_ID`, `ZONE_NAME`, `PROFILE_NAME`, `IMAGE_ID`, `SUBNET_ID`, `SECURITY_GROUP_ID`, `SSH_KEY_ID`
**Optional**: `RESOURCE_GROUP_ID`
**Prerequisites**: VPC, subnet, security group, SSH key must exist
**Provisioning Time**: 3-5 minutes to reach "running" status

### Block Storage Volume Operations

#### List Volume Profiles
```bash
# Mise
mise run volumes:list-profiles

# Bru equivalent
bru run auth/get-iam-token.bru vpc/volumes/list-volume-profiles.bru --env prod
```

**Description**: List volume profiles (IOPS tiers)
**Output**: Profile names, IOPS ranges, capacity limits, use cases
**Profiles**: general-purpose (3 IOPS/GB), 5iops-tier, 10iops-tier, custom

#### List Volumes
```bash
# Mise
mise run volumes:list

# Bru equivalent
bru run auth/get-iam-token.bru vpc/volumes/list-volumes.bru --env prod
```

**Description**: List all block storage volumes
**Output**: Volume names, IDs, capacity, IOPS, status, attachments

#### Get Specific Volume
```bash
# Mise
VOLUME_ID=r006-abc123... mise run volumes:get

# Bru equivalent
VOLUME_ID=r006-abc123... bru run auth/get-iam-token.bru vpc/volumes/get-volume.bru --env prod
```

**Description**: Get volume details
**Required**: `VOLUME_ID`
**Output**: Capacity, IOPS, profile, zone, encryption, attachments

#### Create Volume
```bash
# Mise
VOLUME_NAME="data-volume" ZONE_NAME=us-south-1 VOLUME_CAPACITY=100 VOLUME_PROFILE="general-purpose" mise run volumes:create

# Bru equivalent
VOLUME_NAME="data-volume" ZONE_NAME=us-south-1 VOLUME_CAPACITY=100 VOLUME_PROFILE="general-purpose" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru --env prod
```

**Description**: Create block storage volume
**Required**: `VOLUME_NAME`, `ZONE_NAME`, `VOLUME_CAPACITY` (GB), `VOLUME_PROFILE`
**Optional**: `RESOURCE_GROUP_ID`, `VOLUME_IOPS` (for custom profile)
**Capacity Range**: 10-16,000 GB
**Provisioning Time**: 30-60 seconds

#### Update Volume
```bash
# Mise - Increase capacity
VOLUME_ID=r006-abc VOLUME_CAPACITY=200 mise run volumes:update

# Bru equivalent
VOLUME_ID=r006-abc VOLUME_CAPACITY=200 bru run auth/get-iam-token.bru vpc/volumes/update-volume.bru --env prod

# Mise - Rename volume
VOLUME_ID=r006-abc NEW_VOLUME_NAME="production-data" mise run volumes:update

# Bru equivalent
VOLUME_ID=r006-abc NEW_VOLUME_NAME="production-data" \
  bru run auth/get-iam-token.bru vpc/volumes/update-volume.bru --env prod
```

**Description**: Update volume name or capacity
**Required**: `VOLUME_ID`
**Optional**: `NEW_VOLUME_NAME`, `VOLUME_CAPACITY`
**Note**: Can only increase capacity, never decrease

#### Delete Volume
```bash
# Mise
VOLUME_ID=r006-abc123... mise run volumes:delete

# Bru equivalent
VOLUME_ID=r006-abc123... bru run auth/get-iam-token.bru vpc/volumes/delete-volume.bru --env prod
```

**Description**: Delete volume permanently
**Required**: `VOLUME_ID`
**Prerequisites**: Volume must be detached from all instances
**Warning**: Data loss - cannot be recovered

#### List Volume Attachments
```bash
# Mise
INSTANCE_ID=r006-inst123... mise run volumes:list-attachments

# Bru equivalent
INSTANCE_ID=r006-inst123... bru run auth/get-iam-token.bru vpc/volumes/attachments/list-volume-attachments.bru --env prod
```

**Description**: List volume attachments for an instance
**Required**: `INSTANCE_ID`
**Output**: Boot and data volumes, device IDs, attachment status

#### Get Volume Attachment
```bash
# Mise
INSTANCE_ID=r006-inst VOLUME_ATTACHMENT_ID=r006-attach mise run volumes:get-attachment

# Bru equivalent
INSTANCE_ID=r006-inst VOLUME_ATTACHMENT_ID=r006-attach \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/get-volume-attachment.bru --env prod
```

**Description**: Get specific attachment details
**Required**: `INSTANCE_ID`, `VOLUME_ATTACHMENT_ID`
**Output**: Device info, volume details, deletion behavior

#### Attach Volume to Instance
```bash
# Mise
INSTANCE_ID=r006-inst VOLUME_ID=r006-vol mise run volumes:attach

# Bru equivalent
INSTANCE_ID=r006-inst VOLUME_ID=r006-vol \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/create-volume-attachment.bru --env prod
```

**Description**: Attach volume to instance
**Required**: `INSTANCE_ID`, `VOLUME_ID`
**Prerequisites**: Volume in "available" status, same zone as instance
**Attachment Time**: 10-30 seconds
**Next Steps**: Mount in OS (mkfs.ext4 + mount for Linux)

#### Detach Volume from Instance
```bash
# Mise
INSTANCE_ID=r006-inst VOLUME_ATTACHMENT_ID=r006-attach mise run volumes:detach

# Bru equivalent
INSTANCE_ID=r006-inst VOLUME_ATTACHMENT_ID=r006-attach \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/delete-volume-attachment.bru --env prod
```

**Description**: Detach volume from instance
**Required**: `INSTANCE_ID`, `VOLUME_ATTACHMENT_ID`
**Prerequisites**: Unmount volume in OS first
**Detachment Time**: 10-30 seconds
**Note**: Cannot detach boot volumes

### SSH Key Operations

#### List SSH Keys
```bash
mise run ssh-keys:list
```

**Description**: List all SSH public keys
**Output**: Key IDs, names, types, lengths, fingerprints
**Note**: SSH keys required for Linux instance access

### Floating IP Operations

#### List Floating IPs
```bash
mise run floating-ips:list
```

**Description**: List all floating IPs
**Output**: IP addresses, IDs, targets, zones

#### Get Specific Floating IP
```bash
FLOATING_IP_ID=r006-mno345... mise run floating-ips:get
```

**Description**: Get floating IP details
**Required**: `FLOATING_IP_ID`
**Output**: IP address, target, zone, status

### Load Balancer Operations

#### List Load Balancers
```bash
mise run load-balancers:list
```

**Description**: List all load balancers
**Output**: LB names, IDs, hostnames, statuses, subnets

#### Get Specific Load Balancer
```bash
LOAD_BALANCER_ID=r006-pqr678... mise run load-balancers:get
```

**Description**: Get load balancer details
**Required**: `LOAD_BALANCER_ID`
**Output**: Listeners, pools, health checks, members

## Common Workflows

### Create Complete VPC Environment

```bash
# 1. Get resource group ID
RESOURCE_GROUP_NAME="Default" mise run resource-groups:get-by-name
export RESOURCE_GROUP_ID="<id-from-output>"

# 2. Create VPC
NEW_VPC_NAME="production-vpc" mise run vpc:create
export VPC_ID="<vpc-id-from-output>"

# 3. Create subnets across zones
NEW_SUBNET_NAME="web-tier-zone1" ZONE_NAME=us-south-1 SUBNET_IP_COUNT=256 mise run subnets:create
NEW_SUBNET_NAME="web-tier-zone2" ZONE_NAME=us-south-2 SUBNET_IP_COUNT=256 mise run subnets:create

# 4. Create security group
NEW_SG_NAME="web-servers" mise run security-groups:create
export SECURITY_GROUP_ID="<sg-id-from-output>"

# 5. Add security rules
SECURITY_GROUP_ID=$SECURITY_GROUP_ID mise run security-groups:add-self
SECURITY_GROUP_ID=$SECURITY_GROUP_ID mise run security-groups:add-outbound
SECURITY_GROUP_ID=$SECURITY_GROUP_ID SSH_SOURCE_CIDR="203.0.113.0/24" mise run security-groups:add-ssh
SECURITY_GROUP_ID=$SECURITY_GROUP_ID mise run security-groups:add-https
```

### Provision Instance

```bash
# 1. List available profiles and images
mise run instances:list-profiles
mise run instances:list-images

# 2. List SSH keys
mise run ssh-keys:list

# 3. Create instance
NEW_INSTANCE_NAME="web-server-01" \
  VPC_ID=$VPC_ID \
  ZONE_NAME=us-south-1 \
  PROFILE_NAME=cx2-2x4 \
  IMAGE_ID=r006-<ubuntu-22-04-id> \
  SUBNET_ID=$SUBNET_ID \
  SECURITY_GROUP_ID=$SECURITY_GROUP_ID \
  SSH_KEY_ID=$SSH_KEY_ID \
  mise run instances:create

# 4. Wait for instance to reach "running" (3-5 minutes)
watch -n 10 'INSTANCE_ID=$INSTANCE_ID mise run instances:get'
```

## Tips

### Environment Variables
Set commonly used IDs as environment variables to avoid retyping:
```bash
export VPC_ID="r006-abc123..."
export SECURITY_GROUP_ID="r006-xyz789..."
export SUBNET_ID="r006-def456..."
```

### Shell Aliases
Create aliases for frequently used commands:
```bash
alias vpcs='mise run vpc:list'
alias subnets='mise run subnets:list'
alias sgs='mise run security-groups:list'
alias instances='mise run instances:list'
```

### Pagination
For accounts with many resources, use paginated endpoints:
```bash
# First page
PAGINATION_LIMIT=20 mise run vpc:list-paginated > page1.json

# Extract next token
START_TOKEN=$(jq -r '.next.href | split("start=")[1] | split("&")[0]' page1.json)

# Next page
START_TOKEN=$START_TOKEN PAGINATION_LIMIT=20 mise run vpc:list-paginated > page2.json
```

## Troubleshooting

### Task Not Found
```bash
# List all tasks
mise tasks

# Verify .mise.toml exists
ls -la .mise.toml
```

### Environment Variable Not Passed
```bash
# Verify variable is set
echo $VPC_ID

# Set before running task
export VPC_ID="r006-abc123"
mise run vpc:get
```

### Authentication Fails
```bash
# Check API key is set
echo $IBM_API_KEY

# Re-authenticate
mise run auth
```

---

**Related Documentation**:
- [Main README](../README.md) - Getting started guide
- [CLAUDE.md](../CLAUDE.md) - Complete project documentation
- [Mise Documentation](https://mise.jdx.dev/) - Official mise docs
