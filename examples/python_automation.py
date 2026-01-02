#!/usr/bin/env python3
"""
Python Automation Examples for IBM Cloud VPC Bruno Collection

This script demonstrates various Python automation patterns for
working with the IBM Cloud VPC API via Bruno CLI:

1. Basic request execution and JSON parsing
2. Batch operations (bulk create/delete)
3. Resource inventory and reporting
4. Cost estimation
5. Terraform state comparison
6. Network topology visualization
7. Automated cleanup scripts

Author: Bruno IBM Cloud VPC Collection
"""

import subprocess
import json
import sys
import csv
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


def run_bruno(bru_file: str, env: str = "prod", env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Execute Bruno CLI request and return parsed JSON response.

    Args:
        bru_file: Path to .bru file (e.g., "vpc/list-vpcs.bru")
        env: Environment name (prod or dev)
        env_vars: Optional environment variables to set

    Returns:
        Parsed JSON response

    Example:
        >>> response = run_bruno("vpc/list-vpcs.bru")
        >>> vpcs = response.get("vpcs", [])
        >>> print(f"Found {len(vpcs)} VPCs")
    """
    cmd = [
        "bru", "run",
        "auth/get-iam-token.bru",
        bru_file,
        "--env", env,
        "--output", "json"
    ]

    # Prepare environment
    import os
    env_dict = os.environ.copy()
    if env_vars:
        env_dict.update(env_vars)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        env=env_dict
    )

    return json.loads(result.stdout)


# =============================================================================
# Example 1: Resource Inventory
# =============================================================================

def generate_inventory_report() -> Dict[str, Any]:
    """
    Generate complete inventory of VPC resources.

    Returns:
        Dictionary with resource counts and details

    Example output:
        {
            "vpcs": 5,
            "subnets": 12,
            "instances": 8,
            "security_groups": 15,
            "floating_ips": 6,
            "load_balancers": 2
        }
    """
    print("Generating VPC Resource Inventory...")
    print("=" * 80)

    inventory = {}

    # List all resource types
    resources = [
        ("vpcs", "vpc/list-vpcs.bru"),
        ("subnets", "vpc/subnets/list-subnets.bru"),
        ("instances", "vpc/instances/list-instances.bru"),
        ("security_groups", "vpc/security-groups/list-security-groups.bru"),
        ("floating_ips", "vpc/floating-ips/list-floating-ips.bru"),
        ("load_balancers", "vpc/load-balancers/list-load-balancers.bru"),
    ]

    for resource_type, bru_file in resources:
        try:
            response = run_bruno(bru_file)
            items = response.get(resource_type, [])
            inventory[resource_type] = {
                "count": len(items),
                "items": items
            }
            print(f"✅ {resource_type.capitalize()}: {len(items)}")
        except Exception as e:
            print(f"❌ {resource_type.capitalize()}: Error - {e}")
            inventory[resource_type] = {"count": 0, "items": [], "error": str(e)}

    print("=" * 80)
    print(f"\nTotal Resources: {sum(r['count'] for r in inventory.values())}")

    return inventory


def export_inventory_to_csv(inventory: Dict[str, Any], filename: str = "vpc_inventory.csv"):
    """
    Export resource inventory to CSV file.

    Args:
        inventory: Inventory dictionary from generate_inventory_report()
        filename: Output CSV filename

    Creates CSV with columns:
        Resource Type | ID | Name | Status | Zone | VPC | Created At
    """
    print(f"\nExporting inventory to {filename}...")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Resource Type", "ID", "Name", "Status", "Zone", "VPC", "Created At"])

        for resource_type, data in inventory.items():
            for item in data.get("items", []):
                writer.writerow([
                    resource_type,
                    item.get("id", "N/A"),
                    item.get("name", "N/A"),
                    item.get("status", "N/A"),
                    item.get("zone", {}).get("name", "N/A"),
                    item.get("vpc", {}).get("name", "N/A"),
                    item.get("created_at", "N/A")
                ])

    print(f"✅ Inventory exported to {filename}")


# =============================================================================
# Example 2: Cost Estimation
# =============================================================================

def estimate_vpc_costs(inventory: Dict[str, Any]) -> Dict[str, float]:
    """
    Estimate monthly costs for VPC resources.

    Note: These are approximate costs for us-south region.
    Actual costs vary by region and may change over time.

    Args:
        inventory: Inventory dictionary from generate_inventory_report()

    Returns:
        Dictionary with cost breakdown

    Cost References (approximate, us-south):
        - Instance cx2-2x4: $45/month
        - Instance cx2-4x8: $90/month
        - Floating IP (attached): $0/month
        - Floating IP (unattached): $10/month
        - Load Balancer: $100/month
        - Data Transfer (outbound): $0.09/GB
        - VPC/Subnet: Free
        - Security Groups: Free
    """
    print("\nEstimating Monthly VPC Costs...")
    print("=" * 80)

    costs = {
        "instances": 0.0,
        "floating_ips": 0.0,
        "load_balancers": 0.0,
        "data_transfer": 0.0,
        "total": 0.0
    }

    # Instance costs (profile-based)
    instance_pricing = {
        "cx2-2x4": 45.0,
        "cx2-4x8": 90.0,
        "cx2-8x16": 180.0,
        "bx2-2x8": 60.0,
        "bx2-4x16": 120.0,
        "mx2-4x32": 200.0,
        "mx2-8x64": 400.0,
    }

    instances = inventory.get("instances", {}).get("items", [])
    for instance in instances:
        profile = instance.get("profile", {}).get("name", "unknown")
        cost = instance_pricing.get(profile, 50.0)  # Default $50 if profile unknown
        costs["instances"] += cost
        print(f"  Instance {instance.get('name', 'N/A')} ({profile}): ${cost:.2f}/month")

    # Floating IP costs
    fips = inventory.get("floating_ips", {}).get("items", [])
    unattached_fips = [f for f in fips if not f.get("target")]
    costs["floating_ips"] = len(unattached_fips) * 10.0
    if unattached_fips:
        print(f"  Unattached Floating IPs ({len(unattached_fips)}): ${costs['floating_ips']:.2f}/month")

    # Load balancer costs
    lbs = inventory.get("load_balancers", {}).get("items", [])
    costs["load_balancers"] = len(lbs) * 100.0
    if lbs:
        print(f"  Load Balancers ({len(lbs)}): ${costs['load_balancers']:.2f}/month")

    # Data transfer (estimate 100GB/month per instance)
    if instances:
        estimated_data_gb = len(instances) * 100
        costs["data_transfer"] = estimated_data_gb * 0.09
        print(f"  Data Transfer (est. {estimated_data_gb}GB): ${costs['data_transfer']:.2f}/month")

    # Total
    costs["total"] = sum(v for k, v in costs.items() if k != "total")

    print("=" * 80)
    print(f"Estimated Total Cost: ${costs['total']:.2f}/month")
    print("\nNote: This is an estimate. Actual costs may vary.")
    print("      Does not include storage volumes or network traffic overages.")

    return costs


# =============================================================================
# Example 3: Resource Cleanup
# =============================================================================

def find_resources_by_tag(tag_key: str, tag_value: str) -> List[Dict[str, Any]]:
    """
    Find all resources with specific tag.

    Note: This is a simplified example. IBM Cloud uses CRNs for tagging.
    In practice, you'd query the Global Tagging API.

    Args:
        tag_key: Tag key (e.g., "environment")
        tag_value: Tag value (e.g., "dev")

    Returns:
        List of resources matching tag
    """
    # Placeholder - would integrate with IBM Cloud Global Tagging API
    print(f"Searching for resources with tag {tag_key}={tag_value}...")
    return []


def cleanup_old_resources(days_old: int = 30) -> List[str]:
    """
    Find resources older than N days for cleanup.

    Args:
        days_old: Age threshold in days

    Returns:
        List of resource IDs to potentially delete

    Example:
        >>> old_resources = cleanup_old_resources(days_old=30)
        >>> print(f"Found {len(old_resources)} resources older than 30 days")
    """
    from datetime import datetime, timedelta

    print(f"\nFinding resources older than {days_old} days...")
    print("=" * 80)

    cutoff_date = datetime.now() - timedelta(days=days_old)
    old_resources = []

    # Check instances
    try:
        response = run_bruno("vpc/instances/list-instances.bru")
        instances = response.get("instances", [])

        for instance in instances:
            created_at = instance.get("created_at")
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_date < cutoff_date:
                    age_days = (datetime.now(created_date.tzinfo) - created_date).days
                    old_resources.append({
                        "type": "instance",
                        "id": instance.get("id"),
                        "name": instance.get("name"),
                        "age_days": age_days,
                        "created_at": created_at
                    })
                    print(f"  Instance: {instance.get('name')} ({age_days} days old)")

    except Exception as e:
        print(f"  Error checking instances: {e}")

    print("=" * 80)
    print(f"Found {len(old_resources)} resources older than {days_old} days")
    print("\n⚠️  Review carefully before deleting!")

    return old_resources


# =============================================================================
# Example 4: Network Topology Mapping
# =============================================================================

def map_vpc_topology() -> Dict[str, Any]:
    """
    Build network topology map of VPC infrastructure.

    Returns:
        Dictionary representing VPC topology

    Structure:
        {
            "vpc_id": {
                "name": "my-vpc",
                "subnets": [...],
                "security_groups": [...],
                "instances": [...]
            }
        }
    """
    print("\nMapping VPC Network Topology...")
    print("=" * 80)

    topology = {}

    # Get all VPCs
    vpcs_response = run_bruno("vpc/list-vpcs.bru")
    vpcs = vpcs_response.get("vpcs", [])

    # Get all subnets
    subnets_response = run_bruno("vpc/subnets/list-subnets.bru")
    all_subnets = subnets_response.get("subnets", [])

    # Get all instances
    instances_response = run_bruno("vpc/instances/list-instances.bru")
    all_instances = instances_response.get("instances", [])

    # Get all security groups
    sgs_response = run_bruno("vpc/security-groups/list-security-groups.bru")
    all_sgs = sgs_response.get("security_groups", [])

    # Build topology
    for vpc in vpcs:
        vpc_id = vpc.get("id")
        topology[vpc_id] = {
            "name": vpc.get("name"),
            "id": vpc_id,
            "subnets": [],
            "security_groups": [],
            "instances": []
        }

        # Find subnets in this VPC
        vpc_subnets = [s for s in all_subnets if s.get("vpc", {}).get("id") == vpc_id]
        topology[vpc_id]["subnets"] = vpc_subnets

        # Find security groups in this VPC
        vpc_sgs = [sg for sg in all_sgs if sg.get("vpc", {}).get("id") == vpc_id]
        topology[vpc_id]["security_groups"] = vpc_sgs

        # Find instances in this VPC
        vpc_instances = [i for i in all_instances if i.get("vpc", {}).get("id") == vpc_id]
        topology[vpc_id]["instances"] = vpc_instances

        print(f"\nVPC: {vpc.get('name')} ({vpc_id})")
        print(f"  Subnets: {len(vpc_subnets)}")
        print(f"  Security Groups: {len(vpc_sgs)}")
        print(f"  Instances: {len(vpc_instances)}")

        # Show subnet details
        for subnet in vpc_subnets:
            print(f"    - Subnet: {subnet.get('name')} ({subnet.get('ipv4_cidr_block')})")

        # Show instance details
        for instance in vpc_instances:
            subnet_name = instance.get("primary_network_interface", {}).get("subnet", {}).get("name", "N/A")
            private_ip = instance.get("primary_network_interface", {}).get("primary_ip", {}).get("address", "N/A")
            print(f"    - Instance: {instance.get('name')} ({private_ip}) in subnet {subnet_name}")

    print("=" * 80)
    return topology


def export_topology_to_dot(topology: Dict[str, Any], filename: str = "vpc_topology.dot"):
    """
    Export VPC topology to Graphviz DOT format for visualization.

    Args:
        topology: Topology dictionary from map_vpc_topology()
        filename: Output filename (.dot)

    Usage:
        Generate PNG:
        dot -Tpng vpc_topology.dot -o vpc_topology.png

        Generate SVG:
        dot -Tsvg vpc_topology.dot -o vpc_topology.svg
    """
    print(f"\nExporting topology to {filename}...")

    with open(filename, 'w') as f:
        f.write("digraph VPC_Topology {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [shape=box];\n\n")

        for vpc_id, vpc_data in topology.items():
            vpc_name = vpc_data["name"]

            # VPC node
            f.write(f'  "{vpc_id}" [label="{vpc_name}\\nVPC" shape=folder style=filled fillcolor=lightblue];\n')

            # Subnet nodes
            for subnet in vpc_data["subnets"]:
                subnet_id = subnet.get("id")
                subnet_name = subnet.get("name")
                cidr = subnet.get("ipv4_cidr_block")
                f.write(f'  "{subnet_id}" [label="{subnet_name}\\n{cidr}" style=filled fillcolor=lightgreen];\n')
                f.write(f'  "{vpc_id}" -> "{subnet_id}";\n')

                # Instance nodes in this subnet
                for instance in vpc_data["instances"]:
                    instance_subnet_id = instance.get("primary_network_interface", {}).get("subnet", {}).get("id")
                    if instance_subnet_id == subnet_id:
                        instance_id = instance.get("id")
                        instance_name = instance.get("name")
                        private_ip = instance.get("primary_network_interface", {}).get("primary_ip", {}).get("address", "")
                        f.write(f'  "{instance_id}" [label="{instance_name}\\n{private_ip}" style=filled fillcolor=lightyellow];\n')
                        f.write(f'  "{subnet_id}" -> "{instance_id}";\n')

        f.write("}\n")

    print(f"✅ Topology exported to {filename}")
    print("Generate visualization: dot -Tpng vpc_topology.dot -o vpc_topology.png")


# =============================================================================
# Example 5: Batch Operations
# =============================================================================

def batch_create_instances(
    vpc_id: str,
    subnet_id: str,
    security_group_id: str,
    ssh_key_id: str,
    image_id: str,
    zone_name: str,
    count: int = 3,
    name_prefix: str = "batch-instance",
    profile: str = "cx2-2x4"
) -> List[str]:
    """
    Create multiple instances in batch.

    Args:
        vpc_id: Parent VPC ID
        subnet_id: Subnet ID for all instances
        security_group_id: Security group ID
        ssh_key_id: SSH key ID
        image_id: OS image ID
        zone_name: Availability zone
        count: Number of instances to create
        name_prefix: Name prefix (will append -1, -2, -3, etc.)
        profile: Instance profile

    Returns:
        List of created instance IDs

    Example:
        >>> instance_ids = batch_create_instances(
        ...     vpc_id="r006-abc123",
        ...     subnet_id="r006-def456",
        ...     count=5,
        ...     name_prefix="web-server"
        ... )
        >>> print(f"Created {len(instance_ids)} instances")
    """
    print(f"\nBatch Creating {count} Instances...")
    print("=" * 80)

    instance_ids = []

    for i in range(1, count + 1):
        instance_name = f"{name_prefix}-{i:02d}"

        print(f"\n[{i}/{count}] Creating {instance_name}...")

        try:
            env_vars = {
                "NEW_INSTANCE_NAME": instance_name,
                "VPC_ID": vpc_id,
                "ZONE_NAME": zone_name,
                "PROFILE_NAME": profile,
                "IMAGE_ID": image_id,
                "SUBNET_ID": subnet_id,
                "SECURITY_GROUP_ID": security_group_id,
                "SSH_KEY_ID": ssh_key_id
            }

            response = run_bruno("vpc/instances/create-instance.bru", env_vars=env_vars)
            instance_id = response.get("id")

            if instance_id:
                instance_ids.append(instance_id)
                print(f"  ✅ Created: {instance_id}")
            else:
                print(f"  ❌ Failed: No instance ID in response")

            # Rate limiting delay
            if i < count:
                import time
                time.sleep(2)

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    print("=" * 80)
    print(f"\nCreated {len(instance_ids)}/{count} instances successfully")

    return instance_ids


# =============================================================================
# Main Demonstration
# =============================================================================

def main():
    """Main function demonstrating all automation examples."""
    print("IBM Cloud VPC Python Automation Examples")
    print("=" * 80)

    print("\n[Example 1] Resource Inventory")
    print("-" * 80)
    # inventory = generate_inventory_report()
    # export_inventory_to_csv(inventory)
    print("Run: inventory = generate_inventory_report()")
    print("     export_inventory_to_csv(inventory)")

    print("\n[Example 2] Cost Estimation")
    print("-" * 80)
    # costs = estimate_vpc_costs(inventory)
    print("Run: costs = estimate_vpc_costs(inventory)")

    print("\n[Example 3] Resource Cleanup")
    print("-" * 80)
    # old_resources = cleanup_old_resources(days_old=30)
    print("Run: old_resources = cleanup_old_resources(days_old=30)")

    print("\n[Example 4] Network Topology")
    print("-" * 80)
    # topology = map_vpc_topology()
    # export_topology_to_dot(topology)
    print("Run: topology = map_vpc_topology()")
    print("     export_topology_to_dot(topology)")
    print("     dot -Tpng vpc_topology.dot -o vpc_topology.png")

    print("\n[Example 5] Batch Instance Creation")
    print("-" * 80)
    print("""
Run: instance_ids = batch_create_instances(
    vpc_id="r006-abc123...",
    subnet_id="r006-def456...",
    security_group_id="r006-ghi789...",
    ssh_key_id="r006-jkl012...",
    image_id="r006-mno345...",
    zone_name="us-south-1",
    count=3,
    name_prefix="web-server",
    profile="cx2-2x4"
)
""")

    print("\n" + "=" * 80)
    print("ADDITIONAL AUTOMATION IDEAS")
    print("=" * 80)

    print("""
1. Compliance Checking:
   - Verify all instances have required tags
   - Check security group rules for overly permissive access
   - Ensure all instances are in approved zones

2. Automated Backups:
   - Create snapshots of all instance volumes
   - Export VPC configuration to JSON
   - Save security group rules for disaster recovery

3. Performance Monitoring:
   - Query instance metrics via Cloud Monitoring API
   - Track resource utilization trends
   - Alert on over/under-provisioned instances

4. Cost Optimization:
   - Identify idle instances (no traffic, low CPU)
   - Find unattached floating IPs
   - Suggest right-sizing for over-provisioned instances

5. Security Auditing:
   - Scan security groups for 0.0.0.0/0 rules
   - Check for instances without recent patches
   - Verify encryption settings on volumes

6. Infrastructure as Code:
   - Export current VPC state to Terraform
   - Compare actual vs desired state
   - Generate Terraform import commands

7. CI/CD Integration:
   - Provision test environments
   - Deploy application instances
   - Clean up after test runs
""")


if __name__ == "__main__":
    main()
