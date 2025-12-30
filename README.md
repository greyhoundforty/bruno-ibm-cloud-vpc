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

### VPC Resources (List & Get)
- **VPCs** - List all VPCs or get specific VPC details
- **Subnets** - List all subnets or get specific subnet details
- **Security Groups** - List all security groups or get specific group with all rules
- **Instances (VSIs)** - List all instances or get specific instance details
- **Floating IPs** - List all floating IPs or get specific IP details
- **Load Balancers** - List all load balancers or get specific LB details

**Total**: 13 API endpoints (1 auth + 6 list + 6 get)

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
# Get all VPCs
mise run vpc:list

# Get details for a specific VPC (copy ID from list output)
VPC_ID=r006-5b0702f8-071f-470c-9eeb-2b25ec4ed148 mise run vpc:get

# List subnets in that VPC
mise run subnets:list

# Get details for a specific subnet
SUBNET_ID=r006-abc123... mise run subnets:get
```

#### Example 2: Security Audit

```bash
# List all security groups
mise run security-groups:list

# Get detailed rules for a specific security group
SECURITY_GROUP_ID=r006-21f41a31-5f3d-4b92-a048-e22856d9743d mise run security-groups:get
```

#### Example 3: Instance Inventory

```bash
# List all running instances
mise run instances:list

# Get full details for a specific instance
INSTANCE_ID=r006-xyz789... mise run instances:get
```

## Available Mise Tasks

Run `mise tasks` to see all available commands:

```
auth                    - Get IBM Cloud IAM token
vpc:list                - List all VPCs
vpc:get                 - Get specific VPC by ID
subnets:list            - List all subnets
subnets:get             - Get specific subnet by ID
security-groups:list    - List all security groups
security-groups:get     - Get specific security group by ID
instances:list          - List all instances (VSIs)
instances:get           - Get specific instance by ID
floating-ips:list       - List all floating IPs
floating-ips:get        - Get specific floating IP by ID
load-balancers:list     - List all load balancers
load-balancers:get      - Get specific load balancer by ID
```

## Project Structure

```
bruno-ibm-cloud-vpc/
├── README.md                       # This file
├── CLAUDE.md                       # Development log and technical details
├── bruno.json                      # Collection metadata
├── .mise.toml                      # Task automation configuration
├── environments/
│   ├── prod.bru                    # Production environment (default)
│   └── dev.bru                     # Development environment
├── auth/
│   └── get-iam-token.bru           # IAM authentication
└── vpc/
    ├── get-vpc.bru                 # Get specific VPC
    ├── list-vpcs.bru               # List all VPCs
    ├── security-groups/
    │   ├── list-security-groups.bru
    │   └── get-security-group.bru
    ├── instances/
    │   ├── list-instances.bru
    │   └── get-instance.bru
    ├── floating-ips/
    │   ├── list-floating-ips.bru
    │   └── get-floating-ip.bru
    ├── load-balancers/
    │   ├── list-load-balancers.bru
    │   └── get-load-balancer.bru
    └── subnets/
        ├── list-subnets.bru
        └── get-subnet.bru
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

**Last Updated**: December 30, 2024
**Collection Version**: 1.0
**IBM Cloud VPC API Version**: 2024-12-10
