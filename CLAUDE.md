# CLAUDE.md - IBM Cloud VPC Bruno Collection

## Project Overview

This is a Bruno API collection for interacting with the IBM Cloud VPC REST API. Bruno is a Git-friendly API client that stores requests as plain text `.bru` files, making it perfect for version control and CLI-based workflows.

## Project Structure

```
bruno-ibm-cloud-vpc/
├── bruno.json                              # Collection metadata
├── .mise.toml                              # Task automation configuration
├── environments/
│   ├── dev.bru                            # Development environment
│   └── prod.bru                           # Production environment (default)
├── auth/
│   └── get-iam-token.bru                  # IAM authentication (API key → Bearer token)
└── vpc/
    ├── create-vpc.bru                     # POST - Create VPC
    ├── list-vpcs.bru                      # GET - List all VPCs
    ├── get-vpc.bru                        # GET - Get specific VPC by ID
    ├── subnets/
    │   ├── create-subnet.bru              # POST - Create subnet (IP count method, default)
    │   ├── create-subnet-by-cidr.bru      # POST - Create subnet (CIDR method, alternative)
    │   ├── list-subnets.bru               # GET - List all subnets
    │   └── get-subnet.bru                 # GET - Get specific subnet with resource details
    ├── security-groups/
    │   ├── list-security-groups.bru       # GET - List all security groups
    │   └── get-security-group.bru         # GET - Get specific security group
    ├── instances/
    │   ├── list-instances.bru             # GET - List all instances
    │   └── get-instance.bru               # GET - Get specific instance
    ├── floating-ips/
    │   ├── list-floating-ips.bru          # GET - List all floating IPs
    │   └── get-floating-ip.bru            # GET - Get specific floating IP
    └── load-balancers/
        ├── list-load-balancers.bru        # GET - List all load balancers
        └── get-load-balancer.bru          # GET - Get specific load balancer
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
- [x] Add `vpc/security-groups/list-security-groups.bru`
- [x] Add `vpc/instances/list-instances.bru`
- [x] Add `vpc/floating-ips/list-floating-ips.bru`
- [x] Add `vpc/load-balancers/list-load-balancers.bru`

### Resource Creation (POST requests)
- [x] Create VPC
- [x] Create subnet with CIDR calculation
- [x] Create security group with rules
- [x] Provision VSI (virtual server instance)

### Advanced Features
- [x] Pagination handling for large result sets
- [x] Error handling and retry logic
- [x] Request chaining (create VPC → create subnet → create instance)
- [x] Export to Python/Shell scripts using Bruno's codegen

### Integration Ideas
- [x] Python script to parse Bruno responses and build network diagrams (examples/python_automation.py)
- [x] Cost estimation by counting resources (examples/python_automation.py)
- [ ] Automated testing of VPC configurations
- [ ] Terraform state comparison (Bruno actual vs Terraform expected)

### VPC Resource Expansion (Version 2.0 Target)
- [x] **Phase 1: Block Storage Volumes** (✅ COMPLETE)
  - [x] List volume profiles (IOPS tiers)
  - [x] List/get volumes
  - [x] Create/update/delete volumes
  - [x] Volume attachments (list, get, attach, detach)
  - [x] 10 endpoints, 10 mise tasks
  - [x] Complete documentation in README, MISE.md
- [ ] **Phase 2: Flow Log Collectors** (PLANNED)
  - [ ] List/get/create/update/delete flow log collectors
  - [ ] Support for VPC, subnet, instance, interface targets
  - [ ] Cloud Object Storage integration
  - [ ] ~5 endpoints
- [ ] **Phase 3: Site-to-Site VPN** (PLANNED)
  - [ ] IKE policies (list, get, create, update, delete)
  - [ ] IPsec policies (list, get, create, update, delete)
  - [ ] VPN gateways (list, get, create, update, delete)
  - [ ] VPN connections (list, get, create, update, delete)
  - [ ] ~20 endpoints
- [ ] **Phase 4: Client-to-Site VPN** (PLANNED)
  - [ ] VPN servers (list, get, create, update, delete)
  - [ ] VPN server routes (list, get, create, delete)
  - [ ] VPN server clients (list, get, disconnect)
  - [ ] ~12 endpoints

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

**Last Updated**: January 6, 2026
**Collection Version**: 1.3 (Tags support + Phase 1 Block Storage Volumes complete)
**API Version**: 2024-12-10 (check IBM docs for latest)

## Session Log

### 2026-01-06 - Tags Implementation for All Resources
- **Tags support added to all 6 resource creation endpoints**: VPCs, Subnets, Security Groups, Instances, Volumes
- **Critical discovery: Bruno CLI environment variable quirk**: Inline shell variables (VAR=value bru run) don't work - must use --env-var flags or export
- **Volume creation troubleshooting**: Fixed "invalid_zone" error by switching from inline vars to --env-var flags
- **Important API difference discovered**: Volumes use `user_tags` field while all other resources use `tags` field
- **Environment files updated**: Added TAGS variable to both prod.bru and dev.bru
- **All .bru files updated**: Added tags/user_tags fields to request bodies for 6 creation endpoints
- **README.md comprehensive update**: Added dedicated "Resource Tagging" section with examples, Bruno quirks, cleanup guidance
- **Tag format documented**: Comma-separated quoted strings: `"demo","owner:rtiffany","env:test"`
- **--env-var flag requirement**: Documented that Bruno CLI requires --env-var flags for reliable variable passing
- **Tagging examples added**: All 6 resource types have complete tag usage examples showing --env-var pattern
- **Testing successful**: Volume created with tags verified via IBM Cloud CLI (r006-14ef518a-7944-4b58-995a-7c17ec67e3c7)
- **Tag use cases documented**: Easy cleanup, cost tracking, accountability, automation, organization
- **Collection version bumped**: 1.2 → 1.3 to reflect tags as major feature addition
- **Recent Updates section added**: README now tracks version history with feature additions
- **Bruno CLI behavior documented**: BRUNO_QUIRKS.md created (mentioned in conversation, not in repo), details added to README

### 2026-01-05 - Phase 1: Block Storage Volumes Implementation
- **Implemented 10 volume endpoints**: Complete block storage lifecycle management
- **List endpoints**: list-volume-profiles.bru (IOPS tiers), list-volumes.bru
- **Get endpoint**: get-volume.bru with detailed capacity, IOPS, attachment info
- **Create endpoint**: create-volume.bru with 4 profile types (general-purpose, 5iops-tier, 10iops-tier, custom)
- **Update endpoint**: update-volume.bru for capacity increases (10-16,000 GB) and renaming
- **Delete endpoint**: delete-volume.bru with safety checks and detachment requirements
- **Attachment endpoints**: 4 endpoints (list, get, create, delete) for volume-instance operations
- **Comprehensive documentation**: Each endpoint has detailed docs, prerequisites, examples, error handling, OS mount instructions
- **Environment variables**: Added 8 new volume variables to prod.bru and dev.bru
- **Mise integration**: Added 10 new volume tasks (volumes:list, volumes:create, volumes:attach, etc.)
- **README.md updated**: Added complete Block Storage Volumes section with bru command examples
- **docs/MISE.md updated**: Added volume tasks with bru equivalents following established pattern
- **Volume profiles**: Documented all 4 IOPS tiers with capacity ranges, use cases, cost guidance
- **Post-response scripts**: Comprehensive formatted output for all endpoints with next steps and troubleshooting
- **Total collection size**: 40+ endpoints (30+ existing + 10 volumes)
- **Collection version target**: 2.0 (Phase 1 of 4-phase expansion plan)

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

### 2024-12-30 - fnox Made Optional & Naming Standardization
- **Removed fnox dependency from mise tasks**: All tasks now use plain `bru` commands instead of `fnox run --`
- **Made fnox optional**: Restructured README with Required vs Optional sections, fnox now optional for encrypted secrets
- **Primary method uses export**: Standard `export IBM_API_KEY="..."` approach for environment variables
- **Updated all documentation**: Quick Start, Usage, Troubleshooting sections show both export and fnox methods
- **Testing verified**: All mise tasks work with plain environment variables (no fnox required)
- **Standardized environment variable naming**: Changed `DTS_IBM_API_KEY` → `IBM_API_KEY` (more intuitive)
- **Standardized environment file naming**: Renamed `dts.bru` → `prod.bru` and `natl.bru` → `dev.bru`
- **Updated all configuration**: .mise.toml now uses `--env prod` by default, both environment files use `IBM_API_KEY`
- **Clear dev/prod separation**: Added documentation explaining prod.bru (default) vs dev.bru (alternative)
- **Repository accessibility improved**: Lower barrier to entry, no need to install/learn fnox to get started
- **All changes committed and pushed**: 3 commits total, repository fully updated

### 2024-12-31 - VPC Creation & Subnet Creation Implementation
- **Created VPC creation endpoint** (`vpc/create-vpc.bru`): First POST endpoint with comprehensive verbose output
- **VPC creation tested successfully**: 201 Created response, displays all VPC details, default resources, CSE IPs, next steps
- **Environment variables added**: NEW_VPC_NAME, RESOURCE_GROUP_ID to both prod.bru and dev.bru
- **Mise task added**: vpc:create with automatic authentication flow
- **Created subnet creation endpoints** (2 methods):
  - **Primary method** (`vpc/subnets/create-subnet.bru`): Uses total_ipv4_address_count (IP count)
  - **Alternative method** (`vpc/subnets/create-subnet-by-cidr.bru`): Uses ipv4_cidr_block (CIDR)
- **IP count method made default**: Most users prefer letting IBM Cloud auto-assign CIDR blocks
- **Subnet IP count validation**: Must be power of 2, valid range 8 ≤ value ≤ 8,388,608
- **Enhanced get-subnet.bru**: Categorizes reserved IPs by resource type (instances, load balancers, VPN, other)
- **Instance detection in subnets**: Shows network interface IDs with helpful commands to get full instance details
- **Environment variables added**: NEW_SUBNET_NAME, ZONE_NAME, SUBNET_CIDR, SUBNET_IP_COUNT
- **Mise tasks added**: subnets:create (IP count), subnets:create-by-cidr (CIDR alternative)
- **Fixed Bruno variable case sensitivity**: vpc_id (Bruno var) vs VPC_ID (OS env var) - must match in .bru files
- **Fixed JavaScript environment variable access**: Environment vars not directly accessible in post-response scripts - removed variable references from error messages
- **Subnet creation tested successfully**: 256 IP subnet created with auto-assigned CIDR block
- **Comprehensive documentation**: Both methods fully documented with validation ranges, examples, when to use each

### 2024-12-31 - Security Group Rules Implementation
- **Created 6 security group rule endpoints**: Complete implementation of rule creation for all common use cases
- **Self-reference rule** (`add-rule-self.bru`): Allows all inbound traffic from instances in same security group
- **Outbound all rule** (`add-rule-outbound-all.bru`): Allows all outbound traffic to any destination (0.0.0.0/0)
- **SSH rule** (`add-rule-ssh.bru`): Configurable SSH access (port 22) with customizable source CIDR
- **HTTP rule** (`add-rule-http.bru`): HTTP traffic (port 80) from anywhere
- **HTTPS rule** (`add-rule-https.bru`): HTTPS traffic (port 443) from anywhere with SSL/TLS guidance
- **Generic rule creator** (`create-security-group-rule.bru`): Advanced custom rule creation with full parameter control
- **Environment variables added**: RULE_DIRECTION, RULE_PROTOCOL, REMOTE_CIDR, REMOTE_SG_ID, PORT_MIN, PORT_MAX, SSH_SOURCE_CIDR, ICMP_TYPE, ICMP_CODE
- **Mise tasks added**: 6 new tasks (security-groups:add-self, add-outbound, add-ssh, add-http, add-https, add-rule)
- **Comprehensive documentation**: Each endpoint includes security best practices, use cases, validation, next steps
- **Security warnings**: SSH and HTTP rules include security warnings about exposing services to internet
- **Post-response scripts**: Detailed rule information display with protocol-specific details (ports for TCP/UDP, type/code for ICMP)
- **Production guidance**: HTTPS rule emphasizes encryption requirements, SSL certificate setup, SEO benefits
- **SSH security**: Multiple examples showing restrictive CIDR blocks (office IP, bastion host, VPN) vs open access
- **Total collection**: 26 endpoints (1 auth + 2 resource group + 13 VPC read + 4 VPC create + 1 SG create + 6 SG rules)

### 2026-01-02 - Instance Provisioning & Advanced Features Implementation
- **Created instance provisioning endpoints**: Complete VSI (virtual server instance) creation workflow
- **Helper endpoints created**: list-instance-profiles.bru (compute configs), list-images.bru (OS images), list-ssh-keys.bru (SSH keys)
- **Instance creation endpoint** (`create-instance.bru`): Full instance provisioning with VPC, subnet, security group, SSH key integration
- **Comprehensive documentation**: Profiles, images, SSH keys all documented with recommendations and use cases
- **Profile recommendations**: Development (cx2-2x4), production (cx2-4x8), database (mx2-4x32) with cost estimates
- **Image recommendations**: Ubuntu 22.04 LTS (most popular), RHEL 9 (enterprise), Debian 12 (minimal), Windows Server 2022
- **SSH key guidance**: Key generation, upload, usage, security best practices, troubleshooting
- **Environment variables added**: NEW_INSTANCE_NAME, PROFILE_NAME, IMAGE_ID, PAGINATION_LIMIT, START_TOKEN
- **Mise tasks added**: instances:list-profiles, instances:list-images, ssh-keys:list, instances:create
- **Pagination support**: Created list-vpcs-paginated.bru demonstrating cursor-based pagination with comprehensive docs
- **Pagination example script** (`examples/pagination_example.py`): Complete pagination automation with edge case handling
- **Error handling script** (`examples/error_handling_retry.py`): BrunoClient class with exponential backoff, automatic token refresh, custom exceptions
- **Workflow chaining script** (`examples/workflow_chaining.py`): VPCWorkflow class for automated multi-step infrastructure creation
- **Python automation script** (`examples/python_automation.py`): Resource inventory, cost estimation, cleanup, topology mapping, batch operations
- **Examples README**: Comprehensive documentation of all Python scripts with usage examples and integration patterns
- **Advanced features completed**: All TODO items through "Advanced Features" section now complete
- **Total files created**: 4 new .bru endpoints + 1 paginated endpoint + 4 Python example scripts + examples README
- **Collection size**: 30+ endpoints covering complete VPC lifecycle (create, read, update, delete)
- **Python integration**: 4 production-ready automation scripts (~1,500 lines of code) with error handling, retry logic, workflows

### 2026-01-02 - Documentation Reorganization & Cleanup
- **Streamlined main README**: Reduced from 500+ lines to 240 lines, more scannable and concise
- **Removed excessive emojis**: Eliminated checkmarks and emoji symbols for professional appearance
- **Created docs directory**: Organized supporting documentation separately from main README
- **Created docs/MISE.md**: Complete mise task runner reference with all commands, parameters, workflows, troubleshooting
- **Updated README structure**: Focused on quick start, moved detailed reference to separate docs
- **Improved information architecture**: Main README for getting started, CLAUDE.md for development, docs/MISE.md for task reference
- **Documentation consistency**: All READMEs now follow consistent style (minimal emojis, professional tone)
- **Task list updates**: Marked network diagram and cost estimation as complete in CLAUDE.md TODO
- **Better navigation**: Clear links between README, CLAUDE.md, docs/MISE.md, and examples/README.md
- **Collection version bump**: Updated to v1.2 reflecting documentation improvements

## What Worked

✅ **Bruno post-response scripts**: JavaScript formatting works perfectly for displaying API responses
✅ **Environment variable passing**: `process.env.VPC_ID` pattern works seamlessly for dynamic IDs
✅ **Mise task automation**: Single command execution with auto-authentication is very smooth
✅ **Optional fnox integration**: Works great when needed, but not required for basic usage
✅ **Bruno CLI**: Multi-file execution (auth + request) preserves bearer token across requests
✅ **Comprehensive output**: Post-response scripts provide much better UX than raw JSON
✅ **--env-var flag for tags**: Using --env-var flags reliably passes variables to Bruno (unlike inline shell vars)
✅ **Tags for resource tracking**: All 6 resource types support tags enabling easy cleanup and organization
✅ **API field name differences**: Volumes use user_tags while other resources use tags - handled transparently in .bru files
✅ **Directory structure**: Organized by resource type makes navigation intuitive
✅ **Documentation in docs blocks**: Keeps .bru files self-documenting
✅ **Standard naming conventions**: `IBM_API_KEY`, `prod.bru`, `dev.bru` are more intuitive than custom names
✅ **Git-friendly plain text**: All .bru files are human-readable and easy to version control
✅ **GitHub integration**: gh CLI makes repository creation and management seamless
✅ **Multiple creation methods**: Offering both IP count and CIDR methods gives users flexibility
✅ **IP count as default**: Auto-assigned CIDR blocks simplify subnet creation for most use cases
✅ **Categorized resource display**: Grouping reserved IPs by type (instances, LBs, VPN) improves readability

## What Didn't Work / Challenges

⚠️ **Bruno syntax strict rules**: Comments not allowed in params/headers/vars blocks (must use docs block)
⚠️ **CSE IP structure**: Initially showed "undefined" until correct path (`cse.ip?.address`) was found
⚠️ **Region field**: VPC get endpoint returns region as object but name is sometimes missing (shows "N/A")
⚠️ **Bruno variable case sensitivity**: Environment file variable names (e.g., `vpc_id`) must match exactly when referenced in templates (`{{vpc_id}}`), not the OS env var name (`VPC_ID`)
⚠️ **JavaScript environment variable access**: Environment variables NOT directly accessible in post-response scripts - cannot use `${NEW_SUBNET_NAME}` directly, must avoid or use `bru.getEnvVar()`
⚠️ **409 Conflict on retry**: Subnet names must be unique - failed attempts leave resources that need different names on retry
⚠️ **Bruno inline environment variables**: Inline shell variables (VAR=value bru run) do NOT work - Bruno CLI doesn't read them via `{{process.env.VAR}}`. Must use --env-var flags or export first
⚠️ **Volumes use different tag field**: IBM Cloud API uses `user_tags` for volumes but `tags` for all other resources (VPCs, subnets, security groups, instances)
⚠️ **Variable expansion in --env-var**: Shell variables like $RANDOM don't expand inside --env-var quotes - must pre-expand in shell first
⚠️ **Volume creation "invalid_zone" error**: Initially appeared to be account/zone issue but was actually caused by Bruno not reading inline environment variables

## Next Steps for Next Session

### ✅ Completed

- ✅ All 13 GET endpoints (1 auth + 6 list + 6 get)
- ✅ VPC creation endpoint (vpc/create-vpc.bru) - tested and working
- ✅ Subnet creation endpoints (2 methods):
  - ✅ IP count method (default): create-subnet.bru
  - ✅ CIDR method (alternative): create-subnet-by-cidr.bru
- ✅ Enhanced get-subnet.bru with instance/resource categorization
- ✅ Comprehensive README.md and documentation
- ✅ GitHub repository created and published
- ✅ fnox made optional (not required)
- ✅ Standardized naming (IBM_API_KEY, prod.bru, dev.bru)
- ✅ Mise task automation for all read and create operations
- ✅ Tags support for all 6 resource creation endpoints (VPCs, Subnets, Security Groups, Instances, Volumes)
- ✅ Comprehensive tagging documentation in README with --env-var flag usage
- ✅ Volume tags using user_tags field vs tags field for other resources

### 🎯 Next Session: Continue Resource Creation (POST Endpoints)

**Goal**: Continue implementing POST endpoints for VPC resources.

**Priority Order** (following VPC dependency chain):

#### 1. ~~Create VPC~~ ✅ DONE
#### 2. ~~Create Subnet~~ ✅ DONE (2 methods: IP count and CIDR)

#### 3. Create Security Group (`vpc/security-groups/create-security-group.bru`) - NEXT
**IBM Cloud API**: `POST /v1/security_groups`
**Required Body Parameters**:
- `name` (string): Security group name
- `vpc.id` (string): Parent VPC ID
- `resource_group.id` (string, optional): Resource group ID

**Implementation Plan**:
- Create security group first (empty rules)
- Separate endpoint for adding rules: `create-security-group-rule.bru`
- Environment variables: `NEW_SG_NAME`, `VPC_ID`
- Post-response script: Display group ID and default rules
- Mise task: `security-groups:create`

#### 4. Create Security Group Rule (`vpc/security-groups/create-security-group-rule.bru`)
**IBM Cloud API**: `POST /v1/security_groups/{security_group_id}/rules`
**Required Body Parameters**:
- `direction` (string): "inbound" or "outbound"
- `protocol` (string): "tcp", "udp", "icmp", or "all"
- `ip_version` (string): "ipv4" (default)
- `remote` (string or object): CIDR block or security group ID

**For TCP/UDP**:
- `port_min` (integer): Starting port
- `port_max` (integer): Ending port

**Implementation Plan**:
- Create pre-defined rule templates (SSH, HTTP, HTTPS, All Outbound)
- Environment variables: `SECURITY_GROUP_ID`, `RULE_DIRECTION`, `RULE_PROTOCOL`, `REMOTE_CIDR`
- Post-response script: Display created rule details
- Mise tasks: `security-groups:add-ssh`, `security-groups:add-http`, `security-groups:add-https`

**Example Rule Templates**:
```json
// SSH (port 22)
{
  "direction": "inbound",
  "protocol": "tcp",
  "port_min": 22,
  "port_max": 22,
  "remote": {"cidr_block": "0.0.0.0/0"}
}

// HTTP (port 80)
{
  "direction": "inbound",
  "protocol": "tcp",
  "port_min": 80,
  "port_max": 80,
  "remote": {"cidr_block": "0.0.0.0/0"}
}

// All outbound
{
  "direction": "outbound",
  "protocol": "all",
  "remote": {"cidr_block": "0.0.0.0/0"}
}
```

#### 5. Create Floating IP (`vpc/floating-ips/create-floating-ip.bru`)
**IBM Cloud API**: `POST /v1/floating_ips`
**Required Body Parameters**:
- `name` (string): Floating IP name
- `zone.name` (string): Zone
- `target` (object, optional): Network interface to attach

**Implementation Plan**:
- Two modes: unattached (reserve) or attached (to instance NIC)
- Environment variables: `NEW_FIP_NAME`, `ZONE_NAME`, `TARGET_NETWORK_INTERFACE_ID`
- Post-response script: Display IP address and attachment status
- Mise tasks: `floating-ips:create` (unattached), `floating-ips:create-and-attach`

#### 6. Create Instance (VSI) (`vpc/instances/create-instance.bru`)
**IBM Cloud API**: `POST /v1/instances`
**Most Complex - Required Body Parameters**:
- `name` (string): Instance name
- `vpc.id` (string): Parent VPC ID
- `zone.name` (string): Zone
- `profile.name` (string): Instance profile (e.g., "cx2-2x4")
- `image.id` (string): OS image ID
- `primary_network_interface`:
  - `subnet.id` (string): Subnet ID
  - `security_groups[]` (array): Security group IDs
- `keys[]` (array): SSH key IDs

**Implementation Plan**:
- Requires pre-existing: VPC, subnet, security group, SSH key
- Create helper endpoint: `list-instance-profiles.bru`, `list-images.bru`
- Environment variables: `NEW_INSTANCE_NAME`, `VPC_ID`, `ZONE_NAME`, `PROFILE_NAME`, `IMAGE_ID`, `SUBNET_ID`, `SECURITY_GROUP_ID`, `SSH_KEY_ID`
- Post-response script: Display instance ID, private IP, status
- Mise task: `instances:create`

**Recommended Profile**: `cx2-2x4` (2 vCPU, 4 GB RAM)

### 🎯 Session 3: Resource Deletion (DELETE Endpoints)

**Priority Order** (reverse of creation to handle dependencies):

1. ✅ **Delete Instance** (`instances/delete-instance.bru`)
2. ✅ **Delete Floating IP** (`floating-ips/delete-floating-ip.bru`)
3. ✅ **Delete Subnet** (`subnets/delete-subnet.bru`)
4. ✅ **Delete Security Group** (`security-groups/delete-security-group.bru`)
5. ✅ **Delete VPC** (`vpc/delete-vpc.bru`)

**Common Pattern for All DELETE Endpoints**:
- Method: `DELETE`
- URL: `/v1/{resource}/{id}`
- Query params: `version`, `generation`
- No request body
- Response: 204 No Content (success) or 404 Not Found
- Post-response script: Verify deletion with helpful message
- Add safety checks: confirm resource exists before deletion

### 🎯 Session 4: Advanced Features

#### Filtering Examples
- ✅ Filter subnets by VPC ID
- ✅ Filter instances by zone
- ✅ Filter by resource group
- ✅ Combine multiple filters

#### Pagination Handling
- ✅ Implement `limit` and `start` parameters
- ✅ Follow `next.href` links
- ✅ Show pagination in post-response scripts

#### Error Handling
- ✅ Retry logic for rate limiting
- ✅ Better error messages
- ✅ Request validation

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

### Command Reference for Next Session (Resource Creation)

```bash
# Quick smoke test
mise run auth && mise run vpc:list

# Get resource group ID (needed for VPC creation)
bru run auth/get-iam-token.bru --env prod --output json | jq -r '.body.resource_groups[0].id'

# Create new POST endpoint files (Session 2 focus)
touch vpc/create-vpc.bru
touch vpc/subnets/create-subnet.bru
touch vpc/security-groups/create-security-group.bru
touch vpc/security-groups/create-security-group-rule.bru
touch vpc/floating-ips/create-floating-ip.bru
touch vpc/instances/create-instance.bru

# Helper endpoints for instance creation
touch vpc/instances/list-instance-profiles.bru
touch vpc/instances/list-images.bru

# Update environment variables (add to prod.bru and dev.bru)
# NEW_VPC_NAME, RESOURCE_GROUP_ID, NEW_SUBNET_NAME, ZONE_NAME, SUBNET_CIDR
# NEW_SG_NAME, NEW_FIP_NAME, NEW_INSTANCE_NAME, PROFILE_NAME, IMAGE_ID

# Update mise tasks in .mise.toml
vim .mise.toml
# Add: vpc:create, subnets:create, security-groups:create, etc.

# Test POST endpoint pattern
bru run auth/get-iam-token.bru vpc/create-vpc.bru --env prod
```

### Session 2 Starting Checklist

Before implementing POST endpoints:
1. ✅ Verify all existing GET endpoints still work
2. ✅ Get resource group ID from your IBM Cloud account
3. ✅ Review IBM Cloud VPC API docs for POST endpoint structures
4. ✅ Decide on naming convention for new resources (e.g., "bruno-test-vpc")
5. ✅ Have test VPC/subnet/security group IDs ready for cleanup
6. ✅ Consider creating a "test" resource group for Bruno-created resources
