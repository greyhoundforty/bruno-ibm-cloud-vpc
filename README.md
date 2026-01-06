# IBM Cloud VPC Bruno API Collection

A Git-friendly API collection for IBM Cloud VPC REST API using [Bruno](https://www.usebruno.com/). Store and version control your API requests as plain text `.bru` files.

## Features

- **Version Control Friendly** - Plain text files perfect for Git
- **CLI-First** - Run directly with `bru run` commands
- **Self-Documenting** - Each request includes comprehensive inline documentation
- **Zero Dependencies** - Just Bruno CLI and your API key
- **Optional Task Automation** - Mise integration available for convenience

## What's Included

### Core Operations
- **Authentication** - IAM token generation (API key to Bearer token)
- **Resource Groups** - List and lookup by name
- **VPCs** - List, get details, create
- **Subnets** - List, get details, create (IP count or CIDR methods)
- **Security Groups** - List, get details, create, add rules (SSH, HTTP, HTTPS)
- **Instances** - List, get details, create (with profiles and images)
- **Block Storage Volumes** - List, get, create, update, delete, attach, detach
- **Floating IPs** - List and get details
- **Load Balancers** - List and get details

### Advanced Features
- **Pagination** - Handle large result sets with cursor-based pagination
- **Error Handling** - Python examples with retry logic and exponential backoff
- **Workflow Automation** - Chain requests to create complete infrastructures
- **Batch Operations** - Create multiple resources programmatically

**Total Endpoints**: 40+ (covering complete VPC lifecycle including block storage)

## Prerequisites

### Required

```bash
# Bruno CLI
npm install -g @usebruno/cli

# Verify installation
bru --version
```

### Get IBM Cloud API Key

Create an API key at [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys)

## Quick Start

### 1. Set Your API Key

```bash
export IBM_API_KEY="your-ibm-cloud-api-key"
```

For persistence, add to your shell profile (`~/.bashrc`, `~/.zshrc`):
```bash
echo 'export IBM_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Test Authentication

```bash
bru run auth/get-iam-token.bru --env prod
```

Success output:
```
IAM token obtained successfully
Token expires in: 3600 seconds
```

### 3. List Your VPCs

```bash
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

## Bruno Command Usage

### Authentication Pattern

All Bruno commands follow this pattern - authenticate first, then run your request:

```bash
bru run auth/get-iam-token.bru <request-file> --env prod
```

Running auth and request together ensures the bearer token persists between requests.

### List Resources

```bash
# List all VPCs
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod

# List all subnets
bru run auth/get-iam-token.bru vpc/subnets/list-subnets.bru --env prod

# List all security groups
bru run auth/get-iam-token.bru vpc/security-groups/list-security-groups.bru --env prod

# List all instances (virtual servers)
bru run auth/get-iam-token.bru vpc/instances/list-instances.bru --env prod

# List all floating IPs
bru run auth/get-iam-token.bru vpc/floating-ips/list-floating-ips.bru --env prod

# List all load balancers
bru run auth/get-iam-token.bru vpc/load-balancers/list-load-balancers.bru --env prod

# List all resource groups
bru run auth/get-iam-token.bru resource-groups/list-resource-groups.bru --env prod
```

### Get Specific Resources

Use environment variables to pass resource IDs:

```bash
# Get specific VPC
VPC_ID=r006-abc123 bru run auth/get-iam-token.bru vpc/get-vpc.bru --env prod

# Get specific subnet
SUBNET_ID=r006-def456 bru run auth/get-iam-token.bru vpc/subnets/get-subnet.bru --env prod

# Get specific security group with all rules
SECURITY_GROUP_ID=r006-xyz789 bru run auth/get-iam-token.bru vpc/security-groups/get-security-group.bru --env prod

# Get specific instance
INSTANCE_ID=r006-mno345 bru run auth/get-iam-token.bru vpc/instances/get-instance.bru --env prod
```

### Create Resources

#### Create VPC
```bash
NEW_VPC_NAME="production-vpc" RESOURCE_GROUP_ID="abc123" \
  bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod
```

#### Create Subnet
```bash
# Method 1: IP count (recommended - auto-assigns CIDR)
NEW_SUBNET_NAME="web-subnet" \
  VPC_ID="r006-abc" \
  ZONE_NAME="us-south-1" \
  SUBNET_IP_COUNT=256 \
  bru run auth/get-iam-token.bru vpc/subnets/create-subnet.bru --env prod

# Method 2: Specific CIDR block
NEW_SUBNET_NAME="app-subnet" \
  VPC_ID="r006-abc" \
  ZONE_NAME="us-south-2" \
  SUBNET_CIDR="10.240.1.0/24" \
  bru run auth/get-iam-token.bru vpc/subnets/create-subnet-by-cidr.bru --env prod
```

#### Create Security Group
```bash
NEW_SG_NAME="web-servers" VPC_ID="r006-abc" \
  bru run auth/get-iam-token.bru vpc/security-groups/create-security-group.bru --env prod
```

#### Add Security Group Rules
```bash
# Allow SSH (customize source CIDR for security)
SECURITY_GROUP_ID="r006-xyz" SSH_SOURCE_CIDR="203.0.113.0/24" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-ssh.bru --env prod

# Allow HTTPS
SECURITY_GROUP_ID="r006-xyz" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-https.bru --env prod

# Allow HTTP
SECURITY_GROUP_ID="r006-xyz" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-http.bru --env prod

# Allow all outbound traffic
SECURITY_GROUP_ID="r006-xyz" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-outbound-all.bru --env prod

# Allow instances in same security group to communicate
SECURITY_GROUP_ID="r006-xyz" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-self.bru --env prod
```

#### Create Instance
```bash
# First, list available options
bru run auth/get-iam-token.bru vpc/instances/list-instance-profiles.bru --env prod
bru run auth/get-iam-token.bru vpc/instances/list-images.bru --env prod
bru run auth/get-iam-token.bru vpc/ssh-keys/list-ssh-keys.bru --env prod

# Then create instance
NEW_INSTANCE_NAME="web-server-01" \
  VPC_ID="r006-abc" \
  ZONE_NAME="us-south-1" \
  PROFILE_NAME="cx2-2x4" \
  IMAGE_ID="r006-img-ubuntu" \
  SUBNET_ID="r006-subnet" \
  SECURITY_GROUP_ID="r006-sg" \
  SSH_KEY_ID="r006-key" \
  bru run auth/get-iam-token.bru vpc/instances/create-instance.bru --env prod
```

#### Block Storage Volumes

##### List Volume Profiles (IOPS Tiers)
```bash
# View available performance tiers
bru run auth/get-iam-token.bru vpc/volumes/list-volume-profiles.bru --env prod
```

##### List Volumes
```bash
# List all volumes
bru run auth/get-iam-token.bru vpc/volumes/list-volumes.bru --env prod

# Get specific volume
VOLUME_ID="r006-vol123" bru run auth/get-iam-token.bru vpc/volumes/get-volume.bru --env prod
```

##### Create Volume
```bash
# Create 100GB general-purpose volume
VOLUME_NAME="data-volume" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=100 \
  VOLUME_PROFILE="general-purpose" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru --env prod

# Create high-performance volume
VOLUME_NAME="db-volume" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=500 \
  VOLUME_PROFILE="10iops-tier" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru --env prod
```

**Volume Profiles:**
- `general-purpose` - 3 IOPS/GB (10-16,000 GB) - Most cost-effective
- `5iops-tier` - 5 IOPS/GB (10-9,600 GB) - Production workloads
- `10iops-tier` - 10 IOPS/GB (10-4,800 GB) - High performance
- `custom` - User-defined IOPS (10-16,000 GB) - Precise tuning

##### Update Volume
```bash
# Increase capacity (cannot decrease)
VOLUME_ID="r006-vol123" VOLUME_CAPACITY=200 \
  bru run auth/get-iam-token.bru vpc/volumes/update-volume.bru --env prod

# Rename volume
VOLUME_ID="r006-vol123" NEW_VOLUME_NAME="production-data" \
  bru run auth/get-iam-token.bru vpc/volumes/update-volume.bru --env prod
```

##### Attach Volume to Instance
```bash
# List attachments for an instance
INSTANCE_ID="r006-inst123" \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/list-volume-attachments.bru --env prod

# Attach volume to instance
INSTANCE_ID="r006-inst123" VOLUME_ID="r006-vol123" \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/create-volume-attachment.bru --env prod

# After attaching, mount in OS:
# Linux: sudo mkfs.ext4 /dev/vdb && sudo mount /dev/vdb /mnt/data
# Windows: Disk Management → Online → Initialize → Format
```

##### Detach Volume
```bash
# Detach volume (unmount in OS first!)
INSTANCE_ID="r006-inst123" VOLUME_ATTACHMENT_ID="r006-attach123" \
  bru run auth/get-iam-token.bru vpc/volumes/attachments/delete-volume-attachment.bru --env prod
```

##### Delete Volume
```bash
# Delete volume (must be detached first)
VOLUME_ID="r006-vol123" \
  bru run auth/get-iam-token.bru vpc/volumes/delete-volume.bru --env prod
```

### Pagination for Large Result Sets

```bash
# First page (default limit: 50)
bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod

# Custom page size
PAGINATION_LIMIT=10 bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod

# Next page (use START_TOKEN from previous response)
START_TOKEN="abc123..." PAGINATION_LIMIT=10 \
  bru run auth/get-iam-token.bru vpc/list-vpcs-paginated.bru --env prod
```

## Complete Workflow Example

Create a complete VPC environment with subnets, security groups, and rules:

```bash
# 1. Get resource group ID
RESOURCE_GROUP_NAME="Default" \
  bru run auth/get-iam-token.bru resource-groups/get-resource-group-by-name.bru --env prod
export RESOURCE_GROUP_ID="<id-from-output>"

# 2. Create VPC
NEW_VPC_NAME="production-vpc" RESOURCE_GROUP_ID=$RESOURCE_GROUP_ID \
  bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod
export VPC_ID="<vpc-id-from-output>"

# 3. Create subnets in different zones
NEW_SUBNET_NAME="web-tier-zone1" VPC_ID=$VPC_ID ZONE_NAME="us-south-1" SUBNET_IP_COUNT=256 \
  bru run auth/get-iam-token.bru vpc/subnets/create-subnet.bru --env prod
export SUBNET_1_ID="<subnet-id-from-output>"

NEW_SUBNET_NAME="web-tier-zone2" VPC_ID=$VPC_ID ZONE_NAME="us-south-2" SUBNET_IP_COUNT=256 \
  bru run auth/get-iam-token.bru vpc/subnets/create-subnet.bru --env prod
export SUBNET_2_ID="<subnet-id-from-output>"

# 4. Create security group
NEW_SG_NAME="web-servers" VPC_ID=$VPC_ID \
  bru run auth/get-iam-token.bru vpc/security-groups/create-security-group.bru --env prod
export SECURITY_GROUP_ID="<sg-id-from-output>"

# 5. Add security group rules
SECURITY_GROUP_ID=$SECURITY_GROUP_ID \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-self.bru --env prod

SECURITY_GROUP_ID=$SECURITY_GROUP_ID \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-outbound-all.bru --env prod

SECURITY_GROUP_ID=$SECURITY_GROUP_ID SSH_SOURCE_CIDR="203.0.113.0/24" \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-ssh.bru --env prod

SECURITY_GROUP_ID=$SECURITY_GROUP_ID \
  bru run auth/get-iam-token.bru vpc/security-groups/add-rule-https.bru --env prod

# 6. Verify configuration
SECURITY_GROUP_ID=$SECURITY_GROUP_ID \
  bru run auth/get-iam-token.bru vpc/security-groups/get-security-group.bru --env prod
```

## Environment Configuration

Two environment files are available:

- **environments/prod.bru** (default) - Production account, us-south region
- **environments/dev.bru** - Development/testing, ca-tor region

Switch environments with the `--env` flag:
```bash
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env dev
```

## Using Mise (Optional Convenience)

[Mise](https://mise.jdx.dev/) provides shorter command aliases for Bruno requests. All mise tasks run the same `bru` commands shown above, just with abbreviated syntax.

### Installation
```bash
curl https://mise.run | sh
```

### Example Usage
```bash
# Instead of:
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod

# You can use:
mise run vpc:list

# Instead of:
NEW_VPC_NAME="my-vpc" bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod

# You can use:
NEW_VPC_NAME="my-vpc" mise run vpc:create
```

See [docs/MISE.md](docs/MISE.md) for complete mise task reference.

## Python Automation

The `examples/` directory contains production-ready Python scripts that use `bru` commands via subprocess:

- **pagination_example.py** - Cursor-based pagination for large result sets
- **error_handling_retry.py** - Automatic retry with exponential backoff
- **workflow_chaining.py** - Automated multi-step infrastructure creation
- **python_automation.py** - Inventory, cost estimation, cleanup, topology mapping

Example:
```python
import subprocess
import json

# Run bru command from Python
result = subprocess.run([
    "bru", "run",
    "auth/get-iam-token.bru",
    "vpc/list-vpcs.bru",
    "--env", "prod",
    "--output", "json"
], capture_output=True, text=True, check=True)

vpcs = json.loads(result.stdout).get("vpcs", [])
print(f"Found {len(vpcs)} VPCs")
```

See [examples/README.md](examples/README.md) for complete Python automation guide.

## Troubleshooting

### 401 Unauthorized
Token expired (1 hour validity). Re-authenticate:
```bash
bru run auth/get-iam-token.bru --env prod
```

### API Key Not Found
```bash
# Check if set
echo $IBM_API_KEY

# Set if missing
export IBM_API_KEY="your-api-key"
```

### Bruno Command Not Found
```bash
npm install -g @usebruno/cli
bru --version
```

### Resource Not Found (404)
- Verify resource ID is correct (copy from list command output)
- Check you're in the correct region (see environment files)
- Confirm resource exists in your IBM Cloud account

### Bruno Parsing Errors
Bruno has strict syntax rules:
- Comments NOT allowed in `params:query`, `params:path`, `headers`, `vars` blocks
- Comments ONLY allowed in `docs` and `meta` blocks

## Project Structure

```
bruno-ibm-cloud-vpc/
├── auth/                    # Authentication
│   └── get-iam-token.bru
├── resource-groups/         # Resource group operations
│   ├── list-resource-groups.bru
│   └── get-resource-group-by-name.bru
├── vpc/                     # VPC resources
│   ├── list-vpcs.bru
│   ├── list-vpcs-paginated.bru
│   ├── get-vpc.bru
│   ├── create-vpc.bru
│   ├── subnets/            # Subnet operations
│   ├── security-groups/    # Security group operations
│   ├── instances/          # Instance operations
│   ├── volumes/            # Block storage volume operations
│   │   └── attachments/    # Volume attachment operations
│   ├── ssh-keys/           # SSH key operations
│   ├── floating-ips/       # Floating IP operations
│   └── load-balancers/     # Load balancer operations
├── examples/                # Python automation scripts
├── docs/                    # Additional documentation
│   └── MISE.md             # Mise task runner reference
└── environments/            # Environment configurations
    ├── prod.bru            # Production (default)
    └── dev.bru             # Development
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete project documentation, architecture, session logs
- **[docs/MISE.md](docs/MISE.md)** - Optional mise task runner reference
- **[examples/README.md](examples/README.md)** - Python automation guide
- **[IBM Cloud VPC API](https://cloud.ibm.com/apidocs/vpc)** - Official API reference

## Contributing

Contributions welcome:
1. Fork the repository
2. Add new endpoints following existing `.bru` patterns
3. Update documentation
4. Submit pull requests

## License

MIT License

---

**Collection Version**: 1.2
**IBM Cloud VPC API Version**: 2024-12-10
**Last Updated**: January 2, 2026
