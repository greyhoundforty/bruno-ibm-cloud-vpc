# CLAUDE.md - IBM Cloud VPC Bruno Collection

## Project Overview

This is a Bruno API collection for interacting with the IBM Cloud VPC REST API. Bruno is a Git-friendly API client that stores requests as plain text `.bru` files, making it perfect for version control and CLI-based workflows.

## Project Structure

```
ibm-cloud-vpc/
├── bruno.json                    # Collection metadata
├── environments/
│   ├── dev.bru                  # Development environment (API key, region, endpoints)
│   └── prod.bru                 # Production environment
├── auth/
│   └── get-iam-token.bru        # IAM authentication (API key → Bearer token)
└── vpc/
    ├── list-vpcs.bru            # GET all VPCs
    ├── get-vpc.bru              # GET specific VPC by ID
    └── subnets/
        └── list-subnets.bru     # GET all subnets (with filters)
```

## Key Concepts

### IBM Cloud Authentication Flow
1. **API Key** → stored in `fnox` as `IBM_API_KEY`
2. **IAM Token Endpoint** → POST to `https://iam.cloud.ibm.com/identity/token`
3. **Bearer Token** → received token (valid for 1 hour)
4. **VPC API Requests** → use bearer token in `Authorization: Bearer {token}` header

### IBM Cloud VPC API Basics
- **Base URL**: `https://{region}.iaas.cloud.ibm.com/v1/`
- **Required Query Params**: `version` (API version, e.g., `2024-12-10`) and `generation=2`
- **Regions**: `us-south`, `us-east`, `eu-gb`, `eu-de`, `jp-tok`, `au-syd`, etc.
- **Auth**: Bearer token from IAM in `Authorization` header

## Environment Variables

In `environments/dev.bru`:
- `ibm_api_key`: Your IBM Cloud API key (from `process.env.IBM_API_KEY`)
- `region`: IBM Cloud region (e.g., `us-south`)
- `vpc_endpoint`: Constructed as `https://{{region}}.iaas.cloud.ibm.com`
- `iam_endpoint`: `https://iam.cloud.ibm.com`
- `bearer_token`: Auto-populated by auth request post-response script
- `api_version`: Current API version (check IBM docs for latest)

## Tooling Integration

### fnox (Secret Management)

fnox stores secrets encrypted for each project directory. Secrets are injected as environment variables when running commands with `fnox run --`.

```bash
# Add API key to fnox for this directory
fnox set DTS_IBM_API_KEY your-ibm-cloud-api-key-here

# List secrets for current directory
fnox list

# Run Bruno commands with fnox to inject secrets
fnox run -- bru run auth/get-iam-token.bru --env dts
```

**Important**: Always prefix Bruno commands with `fnox run --` to ensure environment variables are injected.

### mise (Task Runner)

The `.mise.toml` file contains tasks that automatically handle authentication and API calls. Each task runs both the auth request and the target request in a single Bruno execution so the bearer token persists.

```toml
[tasks.auth]
description = "Get IBM Cloud IAM token"
run = "fnox run -- bru run auth/get-iam-token.bru --env dts"

[tasks."vpc:list"]
description = "List all VPCs"
run = "fnox run -- bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env dts"

[tasks."vpc:get"]
description = "Get specific VPC by ID"
run = "fnox run -- bru run auth/get-iam-token.bru vpc/get-vpc.bru --env dts"

[tasks."subnets:list"]
description = "List all subnets"
run = "fnox run -- bru run auth/get-iam-token.bru vpc/subnets/list-subnets.bru --env dts"
```

Usage:
```bash
mise run auth           # Get token only
mise run vpc:list       # Auto-authenticates, then lists VPCs
mise run subnets:list   # Auto-authenticates, then lists subnets
```

**Key Pattern**: Pass multiple `.bru` files to a single `bru run` command. The auth request runs first and sets `bearer_token` via `bru.setEnvVar()`, which persists for subsequent requests in the same execution.

### Bruno CLI Commands
```bash
# Run single request
bru run auth/get-iam-token.bru --env dev

# Run with output
bru run vpc/list-vpcs.bru --env dev --output json

# Run entire collection
bru run . --env dev

# Run folder
bru run vpc/ --env dev
```

## Request Examples

### 1. Authentication
**File**: `auth/get-iam-token.bru`

**What it does**:
- POSTs API key to IAM endpoint
- Receives `access_token` (bearer token)
- Post-response script saves token to `bearer_token` environment variable
- Token valid for 3600 seconds (1 hour)

**Must run first** before any VPC API requests.

### 2. List VPCs
**File**: `vpc/list-vpcs.bru`

**Request**:
```
GET https://us-south.iaas.cloud.ibm.com/v1/vpcs?version=2024-12-10&generation=2
Authorization: Bearer {token}
```

**Response** includes:
- VPC ID, name, status
- Region, resource group
- Default network ACL, security group, routing table
- Creation timestamp

**Optional filters** (query params):
- `resource_group.id`: Filter by resource group
- `limit`: Pagination limit (default 50)
- `start`: Pagination token

### 3. List Subnets
**File**: `vpc/subnets/list-subnets.bru`

**Request**:
```
GET https://us-south.iaas.cloud.ibm.com/v1/subnets?version=2024-12-10&generation=2
Authorization: Bearer {token}
```

**Response** includes:
- Subnet ID, name, status
- VPC reference
- Zone name
- IPv4 CIDR block
- Available vs total IP address counts
- Network ACL, routing table, public gateway references

**Optional filters**:
- `vpc.id`: Filter by VPC
- `zone.name`: Filter by availability zone (e.g., `us-south-1`)
- `resource_group.id`: Filter by resource group

## Common Workflow

1. **Authenticate**: Get bearer token (valid 1 hour)
2. **List VPCs**: See all VPCs in region
3. **List Subnets**: See all subnets (optionally filter by VPC)
4. **Get Specific Resources**: Use IDs from list operations

When you get `401 Unauthorized`, re-run authentication.

## Post-Response Scripts

Bruno supports JavaScript in `script:post-response` blocks:

```javascript
// Extract token and save to environment
if (res.status === 200) {
  const token = res.body.access_token;
  bru.setEnvVar("bearer_token", token);
}

// Pretty-print VPC list
vpcs.forEach(vpc => {
  console.log(`- ${vpc.name} (${vpc.id})`);
});
```

These scripts run automatically after requests complete.

## Next Steps / TODO

### Immediate Additions
- [ ] Add `vpc/security-groups/list-security-groups.bru`
- [ ] Add `vpc/instances/list-instances.bru`
- [ ] Add `vpc/floating-ips/list-floating-ips.bru`
- [ ] Add `vpc/load-balancers/list-load-balancers.bru`

### Resource Creation (POST requests)
- [ ] Create VPC
- [ ] Create subnet with CIDR calculation
- [ ] Create security group with rules
- [ ] Provision VSI (virtual server instance)

### Advanced Features
- [ ] Pagination handling for large result sets
- [ ] Error handling and retry logic
- [ ] Request chaining (create VPC → create subnet → create instance)
- [ ] Export to Python/Shell scripts using Bruno's codegen

### Integration Ideas
- [ ] Python script to parse Bruno responses and build network diagrams
- [ ] Automated testing of VPC configurations
- [ ] Cost estimation by counting resources
- [ ] Terraform state comparison (Bruno actual vs Terraform expected)

## Useful IBM Cloud VPC API Resources

- **API Reference**: https://cloud.ibm.com/apidocs/vpc
- **VPC Concepts**: https://cloud.ibm.com/docs/vpc
- **Regional Endpoints**: https://cloud.ibm.com/docs/vpc?topic=vpc-service-endpoints-for-vpc
- **API Versioning**: https://cloud.ibm.com/docs/vpc?topic=vpc-api-change-log

## Bruno Syntax Rules

**CRITICAL**: Bruno's `.bru` format has strict rules about where comments can appear:

### ✅ Allowed
- Comments inside `docs {}` blocks
- Comments inside `meta {}` blocks

### ❌ NOT Allowed
- Comments inside `params:query {}`, `params:path {}`, `headers {}`, `body:form-urlencoded {}` blocks
- Comments inside `vars {}` blocks in environment files
- Standalone comments outside of blocks (between sections)

### Example - WRONG ❌
```bru
params:query {
  version: {{api_version}}
  generation: 2
  # This comment will cause parsing errors!
}
```

### Example - CORRECT ✅
```bru
params:query {
  version: {{api_version}}
  generation: 2
}

docs {
  # Comments are allowed here
  # Explain optional parameters in the docs section instead
}
```

**Error Pattern**: If you see `Expected ":" ` or `Expected end of input`, check for comments in parameter blocks.

## Tips for Development

1. **Token Management**: Tokens expire after 1 hour. If you get 401 errors, re-authenticate.

2. **API Versioning**: Use the `version` query parameter to lock to a specific API version. Find current version in IBM docs.

3. **Region Selection**: Set in `dev.bru` environment. Each region has separate resources.

4. **Filtering**: Most list endpoints support filtering by resource group, VPC, zone, etc.

5. **Pagination**: Use `limit` and `start` query parameters for large result sets. Response includes `next.href` link.

6. **Post-Response Scripts**: Great for extracting IDs, saving to environment, or formatting output.

7. **Git-Friendly**: All `.bru` files are plain text. Safe to commit everything except `.env` files.

## Python Integration Example

Bruno responses can be parsed in Python scripts:

```python
import subprocess
import json

# Run Bruno request and capture output
result = subprocess.run(
    ["bru", "run", "vpc/list-vpcs.bru", "--env", "dev", "--output", "json"],
    capture_output=True,
    text=True
)

# Parse JSON response
data = json.loads(result.stdout)
vpcs = data["body"]["vpcs"]

for vpc in vpcs:
    print(f"VPC: {vpc['name']} in {vpc['region']['name']}")
```

## Code Style Preferences

When generating new `.bru` files or Python scripts:
- **Comments**: Explain the "why" not just the "what"
- **Python**: Junior-level friendly with detailed inline comments
- **CLI-first**: Prefer terminal commands over GUI instructions
- **mise integration**: Show how to add tasks to `.mise.toml`
- **fnox**: Reference secret management best practices

---

**Last Updated**: December 30, 2024
**Collection Version**: 1.0
**API Version**: 2024-12-10 (check IBM docs for latest)

## Session Log

### 2024-12-30 - Initial Setup & Syntax Fixes
- **Fixed Bruno syntax errors**: Removed all comments from `params:query`, `params:path`, `vars`, and other blocks
- **Configured fnox integration**: Secrets stored with `fnox set DTS_IBM_API_KEY`, accessed via `fnox run --`
- **Created `.mise.toml`**: Tasks for auth, vpc:list, vpc:get, subnets:list with automatic authentication
- **Key discovery**: Multiple `.bru` files in single `bru run` command allows bearer token to persist across requests
- **Tested successfully**: Retrieved 6 VPCs and 21 subnets from us-south region
- **Documentation updates**: Added Bruno syntax rules, fnox/mise integration patterns, and troubleshooting guidance

### 2024-12-30 - VPC ID Parameter & Resource Expansion
- **Enhanced environment configuration**: Added `vpc_id` parameter support via `process.env.VPC_ID`
- **VPC ID passing**: Enabled `VPC_ID=r006-abc... mise run vpc:get` for dynamic VPC retrieval
- **Created 4 new resource types**: security-groups, instances, floating-ips, load-balancers
- **Generated 4 list endpoints**: Each with comprehensive docs, post-response scripts, and filter examples
- **Updated `.mise.toml`**: Added 4 new tasks (security-groups:list, instances:list, floating-ips:list, load-balancers:list)
- **Tested successfully**: Retrieved 14 security groups from us-south region
- **Collection expansion**: 7 total API endpoints (auth + 6 VPC resources) with mise automation

### 2024-12-30 - Individual Get Endpoints & Documentation Complete
- **Fixed get-vpc.bru**: Added comprehensive post-response script to display VPC details, CSE IPs, default resources
- **Created 5 individual get endpoints**: get-security-group.bru, get-instance.bru, get-floating-ip.bru, get-load-balancer.bru, get-subnet.bru
- **Enhanced environment variables**: Added 5 new ID variables (security_group_id, instance_id, floating_ip_id, load_balancer_id, subnet_id)
- **Comprehensive post-response scripts**: Each get endpoint displays detailed, formatted information specific to resource type
- **Security group details**: Shows all rules with direction, protocol, ports, remote IPs/CIDRs, targets
- **Instance details**: Shows compute config, network interfaces, volumes, IPs, security groups, floating IPs
- **Load balancer details**: Shows listeners, pools, health checks, members, public/private IPs
- **Updated `.mise.toml`**: Added 5 new get tasks with environment variable documentation
- **Testing successful**: Verified security-groups:get with 16 rules displayed correctly
- **Final collection**: 13 total endpoints (1 auth + 6 list + 6 get) with full mise automation
- **Created comprehensive README.md**: Complete getting started guide with prerequisites, setup, usage examples
- **Repository ready**: All files documented and ready for GitHub publication

## What Worked

✅ **Bruno post-response scripts**: JavaScript formatting works perfectly for displaying API responses
✅ **Environment variable passing**: `process.env.VPC_ID` pattern works seamlessly for dynamic IDs
✅ **Mise task automation**: Single command execution with auto-authentication is very smooth
✅ **fnox integration**: Secret management works flawlessly, no credentials in files
✅ **Bruno CLI**: Multi-file execution (auth + request) preserves bearer token across requests
✅ **Comprehensive output**: Post-response scripts provide much better UX than raw JSON
✅ **Directory structure**: Organized by resource type makes navigation intuitive
✅ **Documentation in docs blocks**: Keeps .bru files self-documenting

## What Didn't Work / Challenges

⚠️ **Bruno syntax strict rules**: Comments not allowed in params/headers/vars blocks (must use docs block)
⚠️ **CSE IP structure**: Initially showed "undefined" until correct path (`cse.ip?.address`) was found
⚠️ **Region field**: VPC get endpoint returns region as object but name is sometimes missing (shows "N/A")

## Next Steps for Next Session

### Immediate Priorities

1. **Create POST/PUT endpoints** for resource creation:
   - Create VPC
   - Create subnet with CIDR calculation
   - Create security group with rules
   - Provision VSI (virtual server instance)
   - Create floating IP and attach to instance

2. **Add DELETE endpoints** for resource cleanup:
   - Delete floating IP
   - Delete instance
   - Delete subnet
   - Delete security group
   - Delete VPC

3. **Advanced filtering examples**:
   - Add .bru files demonstrating query parameter filters
   - Filter subnets by VPC ID
   - Filter instances by zone
   - Filter by resource group

4. **Pagination handling**:
   - Add examples for large result sets
   - Implement `limit` and `start` parameters
   - Show how to follow `next.href` links

5. **Error handling improvements**:
   - Add retry logic for rate limiting
   - Better error messages in post-response scripts
   - Validation scripts for required parameters

### Long-term Enhancements

- **Python integration scripts**: Parse Bruno JSON output for automation
- **Request chaining**: Create VPC → subnet → instance workflows
- **Cost estimation**: Count resources and estimate monthly costs
- **Terraform comparison**: Compare Bruno actual state vs Terraform desired state
- **Export to shell scripts**: Use Bruno's codegen features
- **Network diagrams**: Parse responses to generate VPC topology visualizations

### Testing Recommendations

Before starting next session:
1. ✅ Run `mise run vpc:list` to verify authentication still works
2. ✅ Test all 6 list endpoints to ensure no API changes
3. ✅ Test all 6 get endpoints with sample IDs
4. ✅ Check IBM Cloud VPC API docs for latest `api_version`

### Command Reference for Next Session

```bash
# Quick smoke test
mise run auth && mise run vpc:list

# Test get endpoints (use IDs from list commands)
VPC_ID=$(mise run vpc:list | grep -o "r006-[a-f0-9-]*" | head -1)
VPC_ID=$VPC_ID mise run vpc:get

# Add new endpoints
touch vpc/create-vpc.bru
touch vpc/instances/create-instance.bru

# Update mise tasks
vim .mise.toml
```
