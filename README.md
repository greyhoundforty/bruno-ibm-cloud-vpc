# IBM Cloud VPC Bruno API Collection

A Git-friendly API collection for the IBM Cloud VPC REST API using [Bruno](https://www.usebruno.com/), a modern API client that stores requests as plain text files instead of binary formats.

## What is This?

This collection provides ready-to-use API requests for managing IBM Cloud VPC infrastructure via the command line. All requests are stored as `.bru` files, making them:
- ✅ **Version control friendly** - Plain text files you can commit to Git
- ✅ **CLI-first** - Run from terminal using `bru run` commands
- ✅ **Simple setup** - Just set environment variables and go
- ✅ **Self-documenting** - Each request includes comprehensive documentation

## What's Included

### Authentication
- IAM token generation (API key → Bearer token)

### Resource Group Management
- **List Resource Groups** - List all resource groups in your account
- **Get by Name** - Find resource group ID by name (for easy lookups)

### VPC Resources (Read Operations)
- **VPCs** - List all VPCs or get specific VPC details
- **Subnets** - List all subnets or get specific subnet details (with instance categorization)
- **Security Groups** - List all security groups or get specific group with all rules
- **Instances (VSIs)** - List all instances or get specific instance details
- **Floating IPs** - List all floating IPs or get specific IP details
- **Load Balancers** - List all load balancers or get specific LB details

### VPC Resources (Create Operations)
- **Create VPC** - Create a new Virtual Private Cloud
- **Create Subnet** - Two methods:
  - IP count method (default) - Specify number of IPs, auto-assign CIDR
  - CIDR method (alternative) - Specify exact CIDR block
- **Create Security Group** - Create empty security group
- **Add Security Group Rules** - Six rule creation methods:
  - Self-reference inbound (allow traffic from same security group)
  - Outbound all (allow all outbound traffic)
  - SSH (port 22) with configurable source CIDR
  - HTTP (port 80) for web servers
  - HTTPS (port 443) for secure web servers
  - Custom rules (advanced - full parameter control)

**Total**: 26 API endpoints (1 auth + 2 resource group + 13 VPC read + 4 VPC create + 1 SG create + 6 SG rules)

## Prerequisites

1. **Bruno CLI** - API client
   ```bash
   npm install -g @usebruno/cli
   ```

2. **IBM Cloud API Key** - Create one at [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys)

### Optional Tools

- **mise** - Task runner for shorter commands (see "Using Mise Task Runner" section)
- **fnox** - Encrypted secret management (alternative to plain environment variables)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/greyhoundforty/bruno-ibm-cloud-vpc.git
cd bruno-ibm-cloud-vpc
```

### 2. Configure Your API Key

Set your IBM Cloud API key as an environment variable:

```bash
export IBM_API_KEY="your-ibm-cloud-api-key-here"
```

To make it permanent, add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
echo 'export IBM_API_KEY="your-ibm-cloud-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Optional**: If you prefer encrypted secret management, you can use [fnox](https://github.com/anthropics/fnox) instead of plain environment variables.

### 3. Test Authentication

Get an IAM bearer token (valid for 1 hour):

```bash
bru run auth/get-iam-token.bru --env prod
```

You should see:
```
✓ IAM token obtained successfully
Token expires in: 3600 seconds
```

### 4. List Your VPCs

```bash
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

You should see all VPCs in your IBM Cloud account with names, IDs, and status.

**💡 Tip**: Running multiple `.bru` files in one command (auth + request) ensures the bearer token persists between requests.

## Usage

### Basic Commands

All commands follow this pattern: authenticate first, then run your request.

```bash
# List all VPCs
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod

# List all subnets
bru run auth/get-iam-token.bru vpc/subnets/list-subnets.bru --env prod

# List all security groups
bru run auth/get-iam-token.bru vpc/security-groups/list-security-groups.bru --env prod

# List all instances
bru run auth/get-iam-token.bru vpc/instances/list-instances.bru --env prod

# List all floating IPs
bru run auth/get-iam-token.bru vpc/floating-ips/list-floating-ips.bru --env prod

# List all load balancers
bru run auth/get-iam-token.bru vpc/load-balancers/list-load-balancers.bru --env prod
```

### Getting Specific Resources

Use environment variables to pass resource IDs:

```bash
# Get specific VPC details
VPC_ID=r006-abc123... bru run auth/get-iam-token.bru vpc/get-vpc.bru --env prod

# Get specific security group with all rules
SECURITY_GROUP_ID=r006-xyz789... bru run auth/get-iam-token.bru vpc/security-groups/get-security-group.bru --env prod

# Get specific instance details
INSTANCE_ID=r006-def456... bru run auth/get-iam-token.bru vpc/instances/get-instance.bru --env prod

# Get specific subnet with resource usage
SUBNET_ID=r006-mno678... bru run auth/get-iam-token.bru vpc/subnets/get-subnet.bru --env prod
```

### Resource Group Management

```bash
# List all resource groups
bru run auth/get-iam-token.bru resource-groups/list-resource-groups.bru --env prod

# Get resource group ID by name
RESOURCE_GROUP_NAME="Default" bru run auth/get-iam-token.bru resource-groups/get-resource-group-by-name.bru --env prod
```

### Common Workflow Examples

#### Example 1: Explore Your VPC Infrastructure

```bash
# List resource groups
bru run auth/get-iam-token.bru resource-groups/list-resource-groups.bru --env prod

# Find resource group ID by name
RESOURCE_GROUP_NAME="Default" bru run auth/get-iam-token.bru resource-groups/get-resource-group-by-name.bru --env prod

# Get all VPCs
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod

# Get details for a specific VPC (copy ID from list output)
VPC_ID=r006-5b0702f8-071f-470c-9eeb-2b25ec4ed148 bru run auth/get-iam-token.bru vpc/get-vpc.bru --env prod

# List subnets in that VPC
bru run auth/get-iam-token.bru vpc/subnets/list-subnets.bru --env prod

# Get details for a specific subnet (shows instances using IPs)
SUBNET_ID=r006-abc123... bru run auth/get-iam-token.bru vpc/subnets/get-subnet.bru --env prod
```

#### Example 2: Create a Complete VPC Environment

```bash
# Step 1: Get resource group ID
RESOURCE_GROUP_NAME="Default" bru run auth/get-iam-token.bru resource-groups/get-resource-group-by-name.bru --env prod
export RESOURCE_GROUP_ID="<id-from-output>"

# Step 2: Create VPC
NEW_VPC_NAME="my-prod-vpc" bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod
export VPC_ID="<vpc-id-from-output>"

# Step 3: Create subnet with 256 IPs (auto-assigned CIDR)
NEW_SUBNET_NAME="web-tier-subnet" \
ZONE_NAME="us-south-1" \
SUBNET_IP_COUNT=256 \
bru run auth/get-iam-token.bru vpc/subnets/create-subnet.bru --env prod

# Alternative: Create subnet with specific CIDR
NEW_SUBNET_NAME="app-tier-subnet" \
ZONE_NAME="us-south-2" \
SUBNET_CIDR="10.240.1.0/24" \
bru run auth/get-iam-token.bru vpc/subnets/create-subnet-by-cidr.bru --env prod

# Step 4: Create security group
NEW_SG_NAME="web-servers-sg" bru run auth/get-iam-token.bru vpc/security-groups/create-security-group.bru --env prod
export SECURITY_GROUP_ID="<sg-id-from-output>"

# Step 5: Add default security group rules
# Allow instances in same security group to communicate
SECURITY_GROUP_ID="<sg-id-from-output>" bru run auth/get-iam-token.bru vpc/security-groups/add-rule-self.bru --env prod

# Allow all outbound traffic (for package updates, etc.)
SECURITY_GROUP_ID="<sg-id-from-output>" bru run auth/get-iam-token.bru vpc/security-groups/add-rule-outbound-all.bru --env prod

# Step 6: Add application-specific rules
# Allow SSH from your office IP (replace with your IP)
SECURITY_GROUP_ID="<sg-id-from-output>" \
SSH_SOURCE_CIDR="203.0.113.0/24" \
bru run auth/get-iam-token.bru vpc/security-groups/add-rule-ssh.bru --env prod

# Allow HTTPS for web servers
SECURITY_GROUP_ID="<sg-id-from-output>" bru run auth/get-iam-token.bru vpc/security-groups/add-rule-https.bru --env prod

# Step 7: View your configured security group with all rules
SECURITY_GROUP_ID="<sg-id-from-output>" bru run auth/get-iam-token.bru vpc/security-groups/get-security-group.bru --env prod
```

#### Example 3: Security Audit

```bash
# List all security groups
bru run auth/get-iam-token.bru vpc/security-groups/list-security-groups.bru --env prod

# Get detailed rules for a specific security group
SECURITY_GROUP_ID=r006-21f41a31-5f3d-4b92-a048-e22856d9743d bru run auth/get-iam-token.bru vpc/security-groups/get-security-group.bru --env prod
```

#### Example 4: Instance Inventory

```bash
# List all running instances
bru run auth/get-iam-token.bru vpc/instances/list-instances.bru --env prod

# Get full details for a specific instance
INSTANCE_ID=r006-xyz789... bru run auth/get-iam-token.bru vpc/instances/get-instance.bru --env prod
```

## Environment Configuration

Two environment files are provided:

### Production Environment (`environments/prod.bru`) - Default
- Used by default in all mise tasks (`--env prod`)
- Configure for your production IBM Cloud account

### Development Environment (`environments/dev.bru`)
- Alternative environment for testing
- Use by specifying `--env dev` in Bruno CLI commands
- Example: `bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env dev`

Both environment files contain:

- `ibm_api_key` - Your IBM Cloud API key (from `IBM_API_KEY` environment variable)
- `region` - IBM Cloud region (default: `us-south`)
- `vpc_endpoint` - VPC API endpoint (auto-constructed)
- `iam_endpoint` - IAM token endpoint
- `bearer_token` - Auto-populated after authentication
- `api_version` - IBM Cloud VPC API version (current: `2024-12-10`)
- Resource IDs - `vpc_id`, `security_group_id`, `instance_id`, etc. (passed via environment variables)

## Authentication Flow

1. **API Key** → Set in `IBM_API_KEY` environment variable
2. **POST** to `https://iam.cloud.ibm.com/identity/token`
3. **Receive** Bearer token (valid 1 hour)
4. **Use** token in `Authorization: Bearer {token}` header for all VPC API calls

When you see `401 Unauthorized` errors, re-authenticate:
```bash
bru run auth/get-iam-token.bru --env prod
```

## Output Examples

### List VPCs Output
```
Found 6 VPC(s):
  - dts-us-south-demo-vpc (r006-5b0702f8-071f-470c-9eeb-2b25ec4ed148)
    Status: available
    Region: us-south
    Created: 2024-11-03T09:48:41Z
  ...
```

### Get VPC Output
```
=== VPC Details ===
Name: dts-us-south-demo-vpc
ID: r006-5b0702f8-071f-470c-9eeb-2b25ec4ed148
Status: available
Created: 2024-11-03T09:48:41Z

--- Default Resources ---
Security Group: wick-pauper-sling-confidant (r006-21f41a31...)
Network ACL: prudent-uniformly-spooky-cognitive (r006-58a95168...)
Routing Table: each-whacky-waviness-hamstring (r006-78748326...)

--- Cloud Service Endpoint Source IPs ---
  Zone us-south-1: 10.22.12.104
  Zone us-south-2: 10.12.161.141
  Zone us-south-3: 10.249.211.112
```

### Get Security Group Output
```
=== Security Group Details ===
Name: wick-pauper-sling-confidant
ID: r006-21f41a31-5f3d-4b92-a048-e22856d9743d

--- Security Rules (16) ---
  Rule 1: r006-33cb82d0-56c4-4ea7-8874-8841782ce4b2
    Direction: outbound
    Protocol: all
    IP Version: ipv4
    Remote: 0.0.0.0/0
  ...
```

## Troubleshooting

### Token Expired (401 Unauthorized)
```bash
# Re-authenticate to get fresh token
mise run auth
```

### API Key Not Found
```bash
# Check if environment variable is set
echo $IBM_API_KEY

# If empty, set it
export IBM_API_KEY="your-api-key-here"

# Or if using fnox
fnox list  # Verify fnox has your API key
fnox set IBM_API_KEY your-api-key-here  # If missing
```

### Bruno Command Not Found
```bash
# Install Bruno CLI
npm install -g @usebruno/cli

# Verify installation
bru --version
```

### Resource Not Found (404)
- Double-check the resource ID (copy from list command output)
- Verify you're in the correct region (check `environments/prod.bru` or `environments/dev.bru`)
- Ensure the resource exists in your IBM Cloud account
- Make sure you're using the correct environment (`--env prod` or `--env dev`)

### Bruno Parsing Errors
Bruno has strict syntax rules:
- ❌ Comments NOT allowed in `params:query`, `params:path`, `headers`, `vars` blocks
- ✅ Comments ONLY allowed in `docs` and `meta` blocks

## Using Mise Task Runner (Optional)

If you prefer shorter commands, you can use [mise](https://mise.jdx.dev/) as a task runner. The `.mise.toml` file defines tasks that automatically handle authentication.

### Installation

```bash
# Install mise from: https://mise.jdx.dev/getting-started.html
curl https://mise.run | sh
```

### Available Tasks

View all available tasks:
```bash
mise tasks
```

### Authentication
```bash
mise run auth                          # Get IBM Cloud IAM token
```

### Resource Groups
```bash
mise run resource-groups:list          # List all resource groups
mise run resource-groups:get-by-name   # Get resource group ID by name (set RESOURCE_GROUP_NAME)
```

### VPC Operations
```bash
mise run vpc:list                      # List all VPCs
mise run vpc:get                       # Get specific VPC by ID (set VPC_ID)
mise run vpc:create                    # Create new VPC (set NEW_VPC_NAME, optionally RESOURCE_GROUP_ID)
```

### Subnet Operations
```bash
mise run subnets:list                  # List all subnets
mise run subnets:get                   # Get specific subnet by ID (set SUBNET_ID)
mise run subnets:create                # Create subnet with IP count (set NEW_SUBNET_NAME, VPC_ID, ZONE_NAME, SUBNET_IP_COUNT)
mise run subnets:create-by-cidr        # Create subnet with CIDR block (set NEW_SUBNET_NAME, VPC_ID, ZONE_NAME, SUBNET_CIDR)
```

### Security Group Operations
```bash
mise run security-groups:list          # List all security groups
mise run security-groups:get           # Get specific security group by ID (set SECURITY_GROUP_ID)
mise run security-groups:create        # Create security group (set NEW_SG_NAME, VPC_ID)
mise run security-groups:add-self      # Add self-reference inbound rule (set SECURITY_GROUP_ID)
mise run security-groups:add-outbound  # Add outbound all rule (set SECURITY_GROUP_ID)
mise run security-groups:add-ssh       # Add SSH inbound rule (set SECURITY_GROUP_ID, optionally SSH_SOURCE_CIDR)
mise run security-groups:add-http      # Add HTTP inbound rule (set SECURITY_GROUP_ID)
mise run security-groups:add-https     # Add HTTPS inbound rule (set SECURITY_GROUP_ID)
mise run security-groups:add-rule      # Add custom rule (set SECURITY_GROUP_ID, RULE_DIRECTION, RULE_PROTOCOL, REMOTE_CIDR)
```

### Instance Operations
```bash
mise run instances:list                # List all instances (VSIs)
mise run instances:get                 # Get specific instance by ID (set INSTANCE_ID)
```

### Floating IP Operations
```bash
mise run floating-ips:list             # List all floating IPs
mise run floating-ips:get              # Get specific floating IP by ID (set FLOATING_IP_ID)
```

### Load Balancer Operations
```bash
mise run load-balancers:list           # List all load balancers
mise run load-balancers:get            # Get specific load balancer by ID (set LOAD_BALANCER_ID)
```

### Usage Example

```bash
# Create a complete VPC environment using mise
RESOURCE_GROUP_NAME="Default" mise run resource-groups:get-by-name
export RESOURCE_GROUP_ID="<id-from-output>"

NEW_VPC_NAME="my-vpc" mise run vpc:create
export VPC_ID="<vpc-id-from-output>"

NEW_SUBNET_NAME="subnet-1" ZONE_NAME="us-south-1" SUBNET_IP_COUNT=256 mise run subnets:create
NEW_SG_NAME="web-sg" mise run security-groups:create

export SECURITY_GROUP_ID="<sg-id-from-output>"
SECURITY_GROUP_ID="$SECURITY_GROUP_ID" mise run security-groups:add-self
SECURITY_GROUP_ID="$SECURITY_GROUP_ID" mise run security-groups:add-outbound
SECURITY_GROUP_ID="$SECURITY_GROUP_ID" mise run security-groups:add-https
```

## IBM Cloud VPC API Resources

- **API Reference**: https://cloud.ibm.com/apidocs/vpc
- **VPC Concepts**: https://cloud.ibm.com/docs/vpc
- **Regional Endpoints**: https://cloud.ibm.com/docs/vpc?topic=vpc-service-endpoints-for-vpc
- **API Versioning**: https://cloud.ibm.com/docs/vpc?topic=vpc-api-change-log

## Development

See [CLAUDE.md](./CLAUDE.md) for:
- Detailed project architecture
- Development workflow
- Session logs and changes
- Bruno syntax rules
- Integration patterns
- Future enhancements

## Contributing

This is a personal API collection, but feel free to:
1. Fork the repository
2. Add new endpoints (follow existing patterns)
3. Update documentation
4. Submit pull requests

## License

MIT License - Feel free to use and modify for your own IBM Cloud VPC automation needs.

---

**Last Updated**: December 31, 2024
**Collection Version**: 1.1
**IBM Cloud VPC API Version**: 2024-12-10
