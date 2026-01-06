#!/bin/bash
# Clean up all VPC resources tagged with "demo" (or custom tag)
#
# Usage:
#   ./examples/cleanup-tagged-resources.sh             # Dry run (list only)
#   ./examples/cleanup-tagged-resources.sh --delete    # Actually delete
#   TAG=my-tag ./examples/cleanup-tagged-resources.sh  # Custom tag
#
# Deletion Order (reverse of creation to handle dependencies):
#   1. Instances (must be deleted before subnets/security groups)
#   2. Volumes (can be deleted independently if detached)
#   3. Security Groups (must be deleted before VPC)
#   4. Subnets (must be deleted before VPC)
#   5. VPCs (deleted last)

set -e

TAG="${TAG:-demo}"
DELETE_MODE="${1}"

echo "Searching for VPC resources tagged with: $TAG"
echo ""

TOTAL_FOUND=0

# 1. Find and delete Instances first (they depend on subnets/security groups)
echo "=== Instances (Virtual Servers) ==="
INSTANCES=$(ibmcloud is instances --output json 2>/dev/null | jq -r ".[] | select(.tags[]? | contains(\"$TAG\")) | .id" || echo "")

if [ -z "$INSTANCES" ]; then
  echo "No instances found with tag: $TAG"
else
  COUNT=$(echo "$INSTANCES" | wc -l | tr -d ' ')
  TOTAL_FOUND=$((TOTAL_FOUND + COUNT))
  echo "Found $COUNT instance(s):"
  for instance in $INSTANCES; do
    instance_name=$(ibmcloud is instance $instance --output json 2>/dev/null | jq -r '.name' || echo "unknown")
    instance_status=$(ibmcloud is instance $instance --output json 2>/dev/null | jq -r '.status' || echo "unknown")
    echo "  - $instance_name ($instance) - Status: $instance_status"

    if [ "$DELETE_MODE" == "--delete" ]; then
      echo "    Deleting instance..."
      ibmcloud is instance-delete $instance --force 2>/dev/null || echo "    Failed to delete (may already be deleted)"
      sleep 2  # Brief pause between deletions
    fi
  done
fi

# 2. Find and delete Volumes (can be deleted if detached)
echo ""
echo "=== Block Storage Volumes ==="
VOLUMES=$(ibmcloud is volumes --output json 2>/dev/null | jq -r ".[] | select(.tags[]? | contains(\"$TAG\")) | .id" || echo "")

if [ -z "$VOLUMES" ]; then
  echo "No volumes found with tag: $TAG"
else
  COUNT=$(echo "$VOLUMES" | wc -l | tr -d ' ')
  TOTAL_FOUND=$((TOTAL_FOUND + COUNT))
  echo "Found $COUNT volume(s):"
  for vol in $VOLUMES; do
    vol_name=$(ibmcloud is volume $vol --output json 2>/dev/null | jq -r '.name' || echo "unknown")
    vol_status=$(ibmcloud is volume $vol --output json 2>/dev/null | jq -r '.status' || echo "unknown")
    vol_attached=$(ibmcloud is volume $vol --output json 2>/dev/null | jq -r '.volume_attachments | length' || echo "0")
    echo "  - $vol_name ($vol) - Status: $vol_status, Attachments: $vol_attached"

    if [ "$DELETE_MODE" == "--delete" ]; then
      if [ "$vol_attached" -gt 0 ]; then
        echo "    ⚠️  Skipping: Volume is attached to an instance (detach first)"
      else
        echo "    Deleting volume..."
        ibmcloud is volume-delete $vol --force 2>/dev/null || echo "    Failed to delete (may already be deleted)"
      fi
    fi
  done
fi

# 3. Find and delete Security Groups (must be deleted before VPC)
echo ""
echo "=== Security Groups ==="
SECURITY_GROUPS=$(ibmcloud is security-groups --output json 2>/dev/null | jq -r ".[] | select(.tags[]? | contains(\"$TAG\")) | .id" || echo "")

if [ -z "$SECURITY_GROUPS" ]; then
  echo "No security groups found with tag: $TAG"
else
  COUNT=$(echo "$SECURITY_GROUPS" | wc -l | tr -d ' ')
  TOTAL_FOUND=$((TOTAL_FOUND + COUNT))
  echo "Found $COUNT security group(s):"
  for sg in $SECURITY_GROUPS; do
    sg_name=$(ibmcloud is security-group $sg --output json 2>/dev/null | jq -r '.name' || echo "unknown")
    sg_vpc=$(ibmcloud is security-group $sg --output json 2>/dev/null | jq -r '.vpc.name' || echo "unknown")
    echo "  - $sg_name ($sg) - VPC: $sg_vpc"

    if [ "$DELETE_MODE" == "--delete" ]; then
      echo "    Deleting security group..."
      ibmcloud is security-group-delete $sg --force 2>/dev/null || echo "    Failed to delete (may be in use or default SG)"
    fi
  done
fi

# 4. Find and delete Subnets (must be deleted before VPC)
echo ""
echo "=== Subnets ==="
SUBNETS=$(ibmcloud is subnets --output json 2>/dev/null | jq -r ".[] | select(.tags[]? | contains(\"$TAG\")) | .id" || echo "")

if [ -z "$SUBNETS" ]; then
  echo "No subnets found with tag: $TAG"
else
  COUNT=$(echo "$SUBNETS" | wc -l | tr -d ' ')
  TOTAL_FOUND=$((TOTAL_FOUND + COUNT))
  echo "Found $COUNT subnet(s):"
  for subnet in $SUBNETS; do
    subnet_name=$(ibmcloud is subnet $subnet --output json 2>/dev/null | jq -r '.name' || echo "unknown")
    subnet_cidr=$(ibmcloud is subnet $subnet --output json 2>/dev/null | jq -r '.ipv4_cidr_block' || echo "unknown")
    subnet_zone=$(ibmcloud is subnet $subnet --output json 2>/dev/null | jq -r '.zone.name' || echo "unknown")
    echo "  - $subnet_name ($subnet) - CIDR: $subnet_cidr, Zone: $subnet_zone"

    if [ "$DELETE_MODE" == "--delete" ]; then
      echo "    Deleting subnet..."
      ibmcloud is subnet-delete $subnet --force 2>/dev/null || echo "    Failed to delete (may have attached resources)"
    fi
  done
fi

# 5. Find and delete VPCs last (all other resources must be deleted first)
echo ""
echo "=== VPCs (Virtual Private Clouds) ==="
VPCS=$(ibmcloud is vpcs --output json 2>/dev/null | jq -r ".[] | select(.tags[]? | contains(\"$TAG\")) | .id" || echo "")

if [ -z "$VPCS" ]; then
  echo "No VPCs found with tag: $TAG"
else
  COUNT=$(echo "$VPCS" | wc -l | tr -d ' ')
  TOTAL_FOUND=$((TOTAL_FOUND + COUNT))
  echo "Found $COUNT VPC(s):"
  for vpc in $VPCS; do
    vpc_name=$(ibmcloud is vpc $vpc --output json 2>/dev/null | jq -r '.name' || echo "unknown")
    vpc_status=$(ibmcloud is vpc $vpc --output json 2>/dev/null | jq -r '.status' || echo "unknown")
    echo "  - $vpc_name ($vpc) - Status: $vpc_status"

    if [ "$DELETE_MODE" == "--delete" ]; then
      echo "    Deleting VPC..."
      ibmcloud is vpc-delete $vpc --force 2>/dev/null || echo "    Failed to delete (may have remaining resources)"
    fi
  done
fi

# Summary
echo ""
echo "========================================="
echo "SUMMARY"
echo "========================================="
echo "Total resources found with tag '$TAG': $TOTAL_FOUND"
echo ""

if [ "$DELETE_MODE" != "--delete" ]; then
  echo "🔍 DRY RUN - No resources were deleted"
  echo ""
  echo "To actually delete these resources, run:"
  echo "  $0 --delete"
  echo ""
  echo "⚠️  WARNING: Deletion happens in dependency order:"
  echo "  1. Instances (deleted first)"
  echo "  2. Volumes (if not attached)"
  echo "  3. Security Groups"
  echo "  4. Subnets"
  echo "  5. VPCs (deleted last)"
else
  echo "✅ Cleanup complete!"
  echo ""
  echo "Note: Some resources may have failed to delete due to:"
  echo "  - Still attached to other resources"
  echo "  - Default resources (cannot be deleted)"
  echo "  - Already deleted in previous run"
  echo ""
  echo "Re-run this script to check for remaining resources:"
  echo "  $0"
fi
