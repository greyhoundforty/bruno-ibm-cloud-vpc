# Python Automation Examples

Production-ready Python scripts demonstrating advanced usage patterns for the IBM Cloud VPC Bruno collection.

## Overview

These scripts show how to integrate Bruno CLI with Python for:
- Pagination handling
- Error handling and retry logic
- Workflow automation (chaining multiple requests)
- Resource inventory and reporting
- Cost estimation
- Batch operations
- Network topology mapping

## Prerequisites

```bash
# Required
- Python 3.8+
- Bruno CLI installed
- IBM Cloud API key (set as IBM_API_KEY environment variable)

# Optional (for visualization)
- Graphviz (for network topology diagrams)
```

## Scripts

### 1. `pagination_example.py`
Demonstrates cursor-based pagination for large result sets.

**Features:**
- Extract pagination cursors from API responses
- Fetch all pages automatically
- Handle pagination edge cases (empty results, expired cursors)
- Performance best practices

**Usage:**
```bash
python3 examples/pagination_example.py
```

**Key Functions:**
- `get_pagination_cursor()` - Extract cursor from response.next.href
- `paginate_list_vpcs()` - Fetch all VPCs across multiple pages
- `demonstrate_pagination_edge_cases()` - Show common scenarios

**When to Use:**
- Listing resources with > 50 items
- Bulk data export
- Inventory reports

---

### 2. `error_handling_retry.py`
Comprehensive error handling with automatic retry logic.

**Features:**
- Exponential backoff for rate limiting (429 errors)
- Automatic token refresh (401 errors)
- Retry logic for transient errors (5xx)
- Custom exception types for different error scenarios

**Usage:**
```bash
python3 examples/error_handling_retry.py
```

**Key Classes:**
- `BrunoClient` - Client with built-in retry logic
- `AuthenticationError` - 401 authentication failures
- `RateLimitError` - 429 rate limit exceeded
- `ResourceNotFoundError` - 404 resource not found
- `ValidationError` - 400/409/422 validation errors

**Example:**
```python
from error_handling_retry import BrunoClient

client = BrunoClient(max_retries=3, initial_retry_delay=1.0)

try:
    vpcs = client.list_vpcs_with_retry()
    print(f"Found {len(vpcs)} VPCs")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except AuthenticationError:
    print("Authentication failed, check IBM_API_KEY")
```

**When to Use:**
- Production automation scripts
- CI/CD pipelines
- Long-running batch operations
- Any script that needs reliability

---

### 3. `workflow_chaining.py`
Automated multi-step workflows with dependency management.

**Features:**
- Sequential request execution
- Automatic dependency resolution (VPC → Subnet → Instance)
- Progress tracking and reporting
- Resource ID extraction and passing between steps
- Error recovery and rollback support

**Usage:**
```bash
python3 examples/workflow_chaining.py
```

**Example:**
```python
from workflow_chaining import VPCWorkflow

# Create complete VPC infrastructure in one script
workflow = VPCWorkflow(
    vpc_name="my-vpc",
    subnet_name="my-subnet",
    sg_name="my-sg",
    instance_name="my-instance",
    zone_name="us-south-1",
    image_id="r006-...",  # Ubuntu 22.04 LTS
    ssh_key_id="r006-...",  # Your SSH key
    instance_profile="cx2-2x4"
)

success = workflow.execute()

if success:
    print(f"VPC: {workflow.vpc_id}")
    print(f"Subnet: {workflow.subnet_id}")
    print(f"Instance: {workflow.instance_id}")
    print(f"Floating IP: {workflow.floating_ip_address}")
```

**Workflow Steps:**
1. Create VPC
2. Create Subnet
3. Create Security Group
4. Add SSH, HTTP, HTTPS, outbound rules
5. Create Instance
6. Create Floating IP (optional)

**When to Use:**
- Automated environment provisioning
- Test environment creation
- Infrastructure deployment
- Development sandbox setup

---

### 4. `python_automation.py`
Collection of automation patterns and use cases.

**Features:**
- Resource inventory reporting
- Cost estimation
- Old resource cleanup
- Network topology mapping
- Batch instance creation
- CSV export
- Graphviz visualization

**Usage:**
```bash
python3 examples/python_automation.py
```

**Key Functions:**

**Resource Inventory:**
```python
from python_automation import generate_inventory_report, export_inventory_to_csv

inventory = generate_inventory_report()
export_inventory_to_csv(inventory, "vpc_inventory.csv")
```

**Cost Estimation:**
```python
from python_automation import estimate_vpc_costs

costs = estimate_vpc_costs(inventory)
print(f"Estimated monthly cost: ${costs['total']:.2f}")
```

**Resource Cleanup:**
```python
from python_automation import cleanup_old_resources

old_resources = cleanup_old_resources(days_old=30)
for resource in old_resources:
    print(f"{resource['name']} is {resource['age_days']} days old")
```

**Network Topology:**
```python
from python_automation import map_vpc_topology, export_topology_to_dot

topology = map_vpc_topology()
export_topology_to_dot(topology, "vpc_topology.dot")

# Generate PNG diagram
# dot -Tpng vpc_topology.dot -o vpc_topology.png
```

**Batch Operations:**
```python
from python_automation import batch_create_instances

instance_ids = batch_create_instances(
    vpc_id="r006-abc123",
    subnet_id="r006-def456",
    security_group_id="r006-ghi789",
    ssh_key_id="r006-jkl012",
    image_id="r006-mno345",
    zone_name="us-south-1",
    count=5,
    name_prefix="web-server",
    profile="cx2-2x4"
)
```

**When to Use:**
- Monthly cost reporting
- Infrastructure audits
- Resource cleanup scripts
- Network documentation
- Bulk provisioning

---

## Common Patterns

### Pattern 1: Execute Bruno Request from Python

```python
import subprocess
import json

def run_bruno(bru_file, env="prod", env_vars=None):
    cmd = ["bru", "run", "auth/get-iam-token.bru", bru_file, "--env", env, "--output", "json"]

    import os
    env_dict = os.environ.copy()
    if env_vars:
        env_dict.update(env_vars)

    result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env_dict)
    return json.loads(result.stdout)

# Usage
response = run_bruno("vpc/list-vpcs.bru")
vpcs = response.get("vpcs", [])
```

### Pattern 2: Pass Environment Variables

```python
# Set environment variables for Bruno request
env_vars = {
    "VPC_ID": "r006-abc123",
    "NEW_SUBNET_NAME": "my-subnet",
    "ZONE_NAME": "us-south-1"
}

response = run_bruno("vpc/subnets/create-subnet.bru", env_vars=env_vars)
subnet_id = response.get("id")
```

### Pattern 3: Extract Nested Values

```python
def extract_value(data, key_path):
    """Extract value from nested dict using dot notation."""
    keys = key_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

# Usage
vpc_name = extract_value(response, "vpc.name")
private_ip = extract_value(response, "primary_network_interface.primary_ip.address")
```

### Pattern 4: Handle Errors

```python
try:
    response = run_bruno("vpc/get-vpc.bru", env_vars={"VPC_ID": vpc_id})
except subprocess.CalledProcessError as e:
    # Bruno CLI failed
    error_output = e.stderr
    print(f"Request failed: {error_output}")
except json.JSONDecodeError as e:
    # JSON parsing failed
    print(f"Invalid JSON response: {e}")
```

### Pattern 5: Retry with Backoff

```python
import time

def run_with_retry(bru_file, max_retries=3):
    delay = 1.0
    for attempt in range(max_retries):
        try:
            return run_bruno(bru_file)
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries} in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
```

---

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy Test Environment

on:
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Bruno CLI
        run: npm install -g @usebruno/cli

      - name: Deploy VPC Infrastructure
        env:
          IBM_API_KEY: ${{ secrets.IBM_API_KEY }}
        run: |
          python3 examples/workflow_chaining.py \
            --vpc-name "pr-${{ github.event.pull_request.number }}" \
            --image-id "r006-..." \
            --ssh-key-id "r006-..."

      - name: Generate Inventory
        run: python3 examples/python_automation.py inventory
```

### Cron Job (Resource Cleanup)

```bash
# crontab -e
# Run cleanup script daily at 2 AM
0 2 * * * cd /path/to/bruno-ibm-cloud-vpc && python3 examples/python_automation.py cleanup --days-old 30 >> /var/log/vpc-cleanup.log 2>&1
```

### Cost Reporting (Weekly)

```bash
#!/bin/bash
# weekly_cost_report.sh

export IBM_API_KEY="your-api-key"

cd /path/to/bruno-ibm-cloud-vpc

python3 -c "
from examples.python_automation import generate_inventory_report, estimate_vpc_costs
inventory = generate_inventory_report()
costs = estimate_vpc_costs(inventory)
print(f'Weekly VPC Cost Report: \${costs[\"total\"]:.2f}/month')
" | mail -s "VPC Cost Report" admin@example.com
```

---

## Troubleshooting

### Issue: `bru: command not found`
**Solution:** Install Bruno CLI:
```bash
npm install -g @usebruno/cli
```

### Issue: `Authentication failed`
**Solution:** Set IBM_API_KEY environment variable:
```bash
export IBM_API_KEY="your-ibm-cloud-api-key"
```

### Issue: `Rate limit exceeded`
**Solution:** Use error_handling_retry.py for automatic backoff:
```python
from error_handling_retry import BrunoClient
client = BrunoClient(max_retries=5, backoff_factor=2.0)
```

### Issue: `json.JSONDecodeError`
**Solution:** Check Bruno CLI output format:
```bash
# Always use --output json
bru run vpc/list-vpcs.bru --env prod --output json
```

### Issue: Workflow fails mid-execution
**Solution:** Check logs for specific step failure, then resume manually or implement rollback

---

## Best Practices

1. **Always use `--output json`** with Bruno CLI for machine-readable output
2. **Set timeouts** for long-running operations
3. **Log all operations** for debugging and auditing
4. **Use retry logic** for production scripts
5. **Validate environment variables** before making API calls
6. **Handle pagination** for resources with > 50 items
7. **Rate limit** batch operations (1-2 second delay between requests)
8. **Clean up resources** created during testing

---

## Additional Resources

- **Bruno Documentation:** https://docs.usebruno.com/
- **IBM Cloud VPC API:** https://cloud.ibm.com/apidocs/vpc
- **Python subprocess:** https://docs.python.org/3/library/subprocess.html

---

## Contributing

To add new examples:

1. Create new Python script in `examples/` directory
2. Follow existing patterns (run_bruno function, error handling)
3. Add comprehensive docstrings
4. Update this README with usage instructions
5. Test with live IBM Cloud account

---

**Last Updated:** January 2, 2026
