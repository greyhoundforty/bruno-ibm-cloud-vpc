# IBM Cloud VPC Bruno API Collection

A Git-friendly API collection for the IBM Cloud VPC REST API using [Bruno](https://www.usebruno.com/), a modern API client that stores requests as plain text files instead of binary formats.

## What is This?

This collection provides ready-to-use API requests for managing IBM Cloud VPC infrastructure via the command line. All requests are stored as `.bru` files, making them:
- ✅ **Version control friendly** - Plain text files you can commit to Git
- ✅ **CLI-first** - Run from terminal using `bru` or `mise` commands
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

### Required

1. **Bruno CLI** - API client
   ```bash
   npm install -g @usebruno/cli
   ```

2. **IBM Cloud API Key** - Create one at [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys)

### Optional (But Recommended)

3. **mise** - Task runner for one-command execution
   ```bash
   # Install from: https://mise.jdx.dev/getting-started.html
   ```

4. **fnox** - Encrypted secret management (alternative to plain environment variables)
   ```bash
   # Install from: https://github.com/anthropics/fnox
   ```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/greyhoundforty/bruno-ibm-cloud-vpc.git
cd bruno-ibm-cloud-vpc
```

### 2. Configure Your API Key

**Option A: Using Environment Variables (Simplest)**

```bash
export IBM_API_KEY="your-ibm-cloud-api-key-here"
```

To make it permanent, add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):
```bash
echo 'export IBM_API_KEY="your-ibm-cloud-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Using fnox (Encrypted Secret Management)**

```bash
fnox set IBM_API_KEY your-ibm-cloud-api-key-here
```

Then use `fnox run --` prefix for all commands:
```bash
fnox run -- mise run auth
```

### 3. Test Authentication

Get an IAM bearer token (valid for 1 hour):

**With mise (recommended):**
```bash
mise run auth
```

**With Bruno CLI directly:**
```bash
bru run auth/get-iam-token.bru --env prod
```

You should see:
```
✓ IAM token obtained successfully
Token expires in: 3600 seconds
```

### 4. List Your VPCs

**With mise:**
```bash
mise run vpc:list
```

**With Bruno CLI:**
```bash
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

You should see all VPCs in your IBM Cloud account with names, IDs, and status.

## Usage

### Using Mise Tasks (Recommended)

Mise tasks automatically handle authentication for you:

```bash
# List all resources
mise run vpc:list
mise run subnets:list
mise run security-groups:list
mise run instances:list
mise run floating-ips:list
mise run load-balancers:list

# Get specific resource by ID
VPC_ID=r006-abc123... mise run vpc:get
SECURITY_GROUP_ID=r006-xyz789... mise run security-groups:get
INSTANCE_ID=r006-def456... mise run instances:get
FLOATING_IP_ID=r006-ghi012... mise run floating-ips:get
LOAD_BALANCER_ID=r006-jkl345... mise run load-balancers:get
SUBNET_ID=r006-mno678... mise run subnets:get
```

### Using Bruno CLI Directly

If you prefer direct Bruno commands without mise:

```bash
# Authenticate first
bru run auth/get-iam-token.bru --env prod

# Run any endpoint (must authenticate first!)
bru run vpc/list-vpcs.bru --env prod

# Run multiple requests in one command (auth + request) - RECOMMENDED
bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod
```

**Important**:
- Make sure `IBM_API_KEY` environment variable is set
- Running multiple files (auth + request) in one command is recommended so the bearer token persists

### Common Workflow Examples

#### Example 1: Explore Your VPC Infrastructure

```bash
# List resource groups
mise run resource-groups:list

# Find resource group ID by name
RESOURCE_GROUP_NAME="Default" mise run resource-groups:get-by-name

# Get all VPCs
mise run vpc:list

# Get details for a specific VPC (copy ID from list output)
VPC_ID=r006-5b0702f8-071f-470c-9eeb-2b25ec4ed148 mise run vpc:get

# List subnets in that VPC
mise run subnets:list

# Get details for a specific subnet (shows instances using IPs)
SUBNET_ID=r006-abc123... mise run subnets:get
```

#### Example 2: Create a Complete VPC Environment

```bash
# Step 1: Get resource group ID
RESOURCE_GROUP_NAME="Default" mise run resource-groups:get-by-name
export RESOURCE_GROUP_ID="<id-from-output>"

# Step 2: Create VPC
NEW_VPC_NAME="my-prod-vpc" mise run vpc:create
export VPC_ID="<vpc-id-from-output>"

# Step 3: Create subnet with 256 IPs (auto-assigned CIDR)
NEW_SUBNET_NAME="web-tier-subnet" \
ZONE_NAME="us-south-1" \
SUBNET_IP_COUNT=256 \
mise run subnets:create

# Alternative: Create subnet with specific CIDR
NEW_SUBNET_NAME="app-tier-subnet" \
ZONE_NAME="us-south-2" \
SUBNET_CIDR="10.240.1.0/24" \
mise run subnets:create-by-cidr

# Step 4: Create security group
NEW_SG_NAME="web-servers-sg" mise run security-groups:create
export SECURITY_GROUP_ID="<sg-id-from-output>"

# Step 5: Add default security group rules
# Allow instances in same security group to communicate
SECURITY_GROUP_ID="<sg-id-from-output>" mise run security-groups:add-self

# Allow all outbound traffic (for package updates, etc.)
SECURITY_GROUP_ID="<sg-id-from-output>" mise run security-groups:add-outbound

# Step 6: Add application-specific rules
# Allow SSH from your office IP (replace with your IP)
SECURITY_GROUP_ID="<sg-id-from-output>" \
SSH_SOURCE_CIDR="203.0.113.0/24" \
mise run security-groups:add-ssh

# Allow HTTPS for web servers
SECURITY_GROUP_ID="<sg-id-from-output>" mise run security-groups:add-https

# Step 7: View your configured security group with all rules
SECURITY_GROUP_ID="<sg-id-from-output>" mise run security-groups:get
```

#### Example 3: Security Audit

```bash
# List all security groups
mise run security-groups:list

# Get detailed rules for a specific security group
SECURITY_GROUP_ID=r006-21f41a31-5f3d-4b92-a048-e22856d9743d mise run security-groups:get
```

#### Example 4: Instance Inventory

```bash
# List all running instances
mise run instances:list

# Get full details for a specific instance
INSTANCE_ID=r006-xyz789... mise run instances:get
```

## Available Mise Tasks

Run `mise tasks` to see all available commands:

### Authentication
```
auth                           - Get IBM Cloud IAM token
```

### Resource Groups
```
resource-groups:list           - List all resource groups
resource-groups:get-by-name    - Get resource group ID by name (set RESOURCE_GROUP_NAME)
```

### VPC Operations
```
vpc:list                       - List all VPCs
vpc:get                        - Get specific VPC by ID (set VPC_ID)
vpc:create                     - Create new VPC (set NEW_VPC_NAME, optionally RESOURCE_GROUP_ID)
```

### Subnet Operations
```
subnets:list                   - List all subnets
subnets:get                    - Get specific subnet by ID (set SUBNET_ID)
subnets:create                 - Create subnet with IP count (set NEW_SUBNET_NAME, VPC_ID, ZONE_NAME, SUBNET_IP_COUNT)
subnets:create-by-cidr         - Create subnet with CIDR block (set NEW_SUBNET_NAME, VPC_ID, ZONE_NAME, SUBNET_CIDR)
```

### Security Group Operations
```
security-groups:list           - List all security groups
security-groups:get            - Get specific security group by ID (set SECURITY_GROUP_ID)
security-groups:create         - Create security group (set NEW_SG_NAME, VPC_ID)
security-groups:add-self       - Add self-reference inbound rule (set SECURITY_GROUP_ID)
security-groups:add-outbound   - Add outbound all rule (set SECURITY_GROUP_ID)
security-groups:add-ssh        - Add SSH inbound rule (set SECURITY_GROUP_ID, optionally SSH_SOURCE_CIDR)
security-groups:add-http       - Add HTTP inbound rule (set SECURITY_GROUP_ID)
security-groups:add-https      - Add HTTPS inbound rule (set SECURITY_GROUP_ID)
security-groups:add-rule       - Add custom rule (set SECURITY_GROUP_ID, RULE_DIRECTION, RULE_PROTOCOL, REMOTE_CIDR)
```

### Instance Operations
```
instances:list                 - List all instances (VSIs)
instances:get                  - Get specific instance by ID (set INSTANCE_ID)
```

### Floating IP Operations
```
floating-ips:list              - List all floating IPs
floating-ips:get               - Get specific floating IP by ID (set FLOATING_IP_ID)
```

### Load Balancer Operations
```
load-balancers:list            - List all load balancers
load-balancers:get             - Get specific load balancer by ID (set LOAD_BALANCER_ID)
```

## Project Structure

```
bruno-ibm-cloud-vpc/
├── README.md                              # This file
├── CLAUDE.md                              # Development log and technical details
├── bruno.json                             # Collection metadata
├── .mise.toml                             # Task automation configuration
├── environments/
│   ├── prod.bru                           # Production environment (default)
│   └── dev.bru                            # Development environment
├── auth/
│   └── get-iam-token.bru                  # IAM authentication
├── resource-groups/
│   ├── list-resource-groups.bru           # List all resource groups
│   └── get-resource-group-by-name.bru     # Get RG ID by name
└── vpc/
    ├── create-vpc.bru                     # Create VPC
    ├── list-vpcs.bru                      # List all VPCs
    ├── get-vpc.bru                        # Get specific VPC
    ├── subnets/
    │   ├── create-subnet.bru              # Create subnet (IP count method)
    │   ├── create-subnet-by-cidr.bru      # Create subnet (CIDR method)
    │   ├── list-subnets.bru               # List all subnets
    │   └── get-subnet.bru                 # Get subnet with resource details
    ├── security-groups/
    │   ├── create-security-group.bru      # Create security group
    │   ├── add-rule-self.bru              # Add self-reference inbound rule
    │   ├── add-rule-outbound-all.bru      # Add outbound all rule
    │   ├── add-rule-ssh.bru               # Add SSH inbound rule
    │   ├── add-rule-http.bru              # Add HTTP inbound rule
    │   ├── add-rule-https.bru             # Add HTTPS inbound rule
    │   ├── create-security-group-rule.bru # Create custom rule (advanced)
    │   ├── list-security-groups.bru       # List all security groups
    │   └── get-security-group.bru         # Get security group with rules
    ├── instances/
    │   ├── list-instances.bru             # List all instances
    │   └── get-instance.bru               # Get specific instance
    ├── floating-ips/
    │   ├── list-floating-ips.bru          # List all floating IPs
    │   └── get-floating-ip.bru            # Get specific floating IP
    └── load-balancers/
        ├── list-load-balancers.bru        # List all load balancers
        └── get-load-balancer.bru          # Get specific load balancer
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

## IBM Cloud Regions

Available regions you can configure in environment files (`environments/prod.bru` or `environments/dev.bru`):
- `us-south` (Dallas)
- `us-east` (Washington DC)
- `eu-gb` (London)
- `eu-de` (Frankfurt)
- `jp-tok` (Tokyo)
- `au-syd` (Sydney)
- `jp-osa` (Osaka)
- `ca-tor` (Toronto)
- `br-sao` (São Paulo)

## Authentication Flow

1. **API Key** → Set in `IBM_API_KEY` environment variable
2. **POST** to `https://iam.cloud.ibm.com/identity/token`
3. **Receive** Bearer token (valid 1 hour)
4. **Use** token in `Authorization: Bearer {token}` header for all VPC API calls

When you see `401 Unauthorized` errors, re-run `mise run auth`.

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
