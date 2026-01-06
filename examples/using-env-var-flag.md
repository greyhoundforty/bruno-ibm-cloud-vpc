# Using Bruno's --env-var Flag for Tags

This guide shows how to use Bruno's `--env-var` flag to override environment variables, particularly useful for adding tags to resources.

## Bruno CLI Environment Variable Options

```bash
bru run --help | grep '-env'
  --env                Environment variables                [string]
  --env-file           Path to environment file (.bru or .json)
  --env-var            Overwrite a single environment variable
```

## Methods for Setting Environment Variables

### Method 1: Shell Environment Variables (Most Common)

Set environment variables directly in your shell:

```bash
TAGS='"demo","owner:rtiffany"' \
  VOLUME_NAME="test-volume" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=100 \
  VOLUME_PROFILE="general-purpose" \
  RESOURCE_GROUP_ID="ac83304b2fb6492e95995812da85b653" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru --env prod
```

### Method 2: Using --env-var Flag (Single Variable Override)

Override a single environment variable:

```bash
bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru \
  --env prod \
  --env-var 'TAGS="demo","bruno-test"'
```

**Note:** The `--env-var` flag is useful for overriding values already defined in your environment file, but shell environment variables are usually simpler for setting multiple values.

### Method 3: Multiple --env-var Flags

You can use multiple `--env-var` flags to set multiple variables:

```bash
bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru \
  --env prod \
  --env-var 'VOLUME_NAME=demo-volume' \
  --env-var 'ZONE_NAME=us-south-1' \
  --env-var 'VOLUME_CAPACITY=100' \
  --env-var 'VOLUME_PROFILE=general-purpose' \
  --env-var 'RESOURCE_GROUP_ID=ac83304b2fb6492e95995812da85b653' \
  --env-var 'TAGS="demo","owner:ryan"'
```

### Method 4: Combining Shell Vars and --env-var

You can combine both approaches:

```bash
# Set most variables in shell
VOLUME_NAME="test-volume" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=100 \
  VOLUME_PROFILE="general-purpose" \
  RESOURCE_GROUP_ID="ac83304b2fb6492e95995812da85b653" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru \
    --env prod \
    --env-var 'TAGS="demo","bruno-override"'
```

## Tag Format Examples

### Single Tag
```bash
--env-var 'TAGS="demo"'
```

### Multiple Tags
```bash
--env-var 'TAGS="demo","test","owner:ryan"'
```

### Key-Value Tags
```bash
--env-var 'TAGS="demo","env:dev","team:cde","cost-center:78003"'
```

### Date-Based Tags
```bash
--env-var 'TAGS="demo","created:2026-01-05","expires:2026-01-12"'
```

## Complete Examples by Resource Type

### Create VPC with Tags

```bash
bru run auth/get-iam-token.bru vpc/create-vpc.bru \
  --env prod \
  --env-var 'NEW_VPC_NAME=demo-vpc' \
  --env-var 'RESOURCE_GROUP_ID=ac83304b2fb6492e95995812da85b653' \
  --env-var 'TAGS="demo","vpc-test","owner:ryan"'
```

### Create Subnet with Tags

```bash
bru run auth/get-iam-token.bru vpc/subnets/create-subnet.bru \
  --env prod \
  --env-var 'NEW_SUBNET_NAME=demo-subnet' \
  --env-var 'VPC_ID=r006-abc123...' \
  --env-var 'ZONE_NAME=us-south-1' \
  --env-var 'SUBNET_IP_COUNT=256' \
  --env-var 'TAGS="demo","subnet-test"'
```

### Create Security Group with Tags

```bash
bru run auth/get-iam-token.bru vpc/security-groups/create-security-group.bru \
  --env prod \
  --env-var 'NEW_SG_NAME=demo-sg' \
  --env-var 'VPC_ID=r006-abc123...' \
  --env-var 'TAGS="demo","sg-test","allows-ssh"'
```

### Create Instance with Tags

```bash
bru run auth/get-iam-token.bru vpc/instances/create-instance.bru \
  --env prod \
  --env-var 'NEW_INSTANCE_NAME=demo-instance' \
  --env-var 'VPC_ID=r006-abc123...' \
  --env-var 'ZONE_NAME=us-south-1' \
  --env-var 'PROFILE_NAME=cx2-2x4' \
  --env-var 'IMAGE_ID=r006-xyz789...' \
  --env-var 'SUBNET_ID=r006-def456...' \
  --env-var 'SECURITY_GROUP_ID=r006-ghi789...' \
  --env-var 'SSH_KEY_ID=r006-jkl012...' \
  --env-var 'RESOURCE_GROUP_ID=ac83304b2fb6492e95995812da85b653' \
  --env-var 'TAGS="demo","test-instance","os:ubuntu"'
```

### Create Volume with Tags

```bash
bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru \
  --env prod \
  --env-var 'VOLUME_NAME=demo-volume' \
  --env-var 'ZONE_NAME=us-south-1' \
  --env-var 'VOLUME_CAPACITY=100' \
  --env-var 'VOLUME_PROFILE=general-purpose' \
  --env-var 'RESOURCE_GROUP_ID=ac83304b2fb6492e95995812da85b653' \
  --env-var 'TAGS="demo","volume-test","size:100gb"'
```

## Using with mise Tasks

mise tasks automatically pass through shell environment variables:

```bash
# Simple approach - set shell variables
TAGS='"demo","mise-test"' \
  VOLUME_NAME="demo-volume" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=100 \
  VOLUME_PROFILE="general-purpose" \
  RESOURCE_GROUP_ID="ac83304b2fb6492e95995812da85b653" \
  mise run volumes:create
```

**Note:** The `--env-var` flag is a `bru` CLI flag, not a `mise` flag, so you cannot use it directly with `mise run` commands.

## Recommended Approach

For most use cases, **shell environment variables** are the simplest:

```bash
# Easy to read, easy to modify
TAGS='"demo","owner:ryan"' \
  VOLUME_NAME="test" \
  ZONE_NAME="us-south-1" \
  VOLUME_CAPACITY=100 \
  VOLUME_PROFILE="general-purpose" \
  RESOURCE_GROUP_ID="ac83304b2fb6492e95995812da85b653" \
  bru run auth/get-iam-token.bru vpc/volumes/create-volume.bru --env prod
```

Use `--env-var` when:
- You need to override a single variable
- The variable contains special characters that are hard to escape in shell
- You're scripting and want explicit control over each variable

## Tag Best Practices

1. **Always include "demo"** tag for easy cleanup
2. **Add owner tag** for accountability: `"owner:rtiffany"`
3. **Include creation date**: `"created:2026-01-05"`
4. **Add purpose/project**: `"project:vpc-testing"`
5. **Use consistent key:value format**: `"env:dev"`, `"team:cde"`

## Cleanup Tagged Resources

Once tagged, cleanup is easy:

```bash
# Find all demo resources
./examples/cleanup-tagged-resources.sh

# Delete all demo resources
./examples/cleanup-tagged-resources.sh --delete

# Custom tag
TAG="my-project" ./examples/cleanup-tagged-resources.sh --delete
```

## Troubleshooting

### Tags Not Appearing

If tags don't appear on created resources:

1. **Check tag format** - Must be comma-separated quoted strings
   - ✅ `TAGS='"demo","test"'`
   - ❌ `TAGS="demo,test"`

2. **Check JSON rendering** - Use `--output json` to see request body
   ```bash
   bru run ... --env prod --output json | jq '.request.data'
   ```

3. **Verify API field name** - IBM Cloud VPC uses `"tags"` not `"user_tags"`

### Shell Escaping Issues

If you get shell errors:

```bash
# Wrong - shell interprets quotes incorrectly
TAGS="demo","test" bru run ...

# Correct - outer single quotes, inner double quotes
TAGS='"demo","test"' bru run ...

# Alternative - escape inner quotes
TAGS="\"demo\",\"test\"" bru run ...
```

## Summary

- ✅ **Shell variables**: Best for setting multiple values
- ✅ **--env-var flag**: Best for single overrides
- ✅ **mise tasks**: Use shell variables (--env-var doesn't work with mise)
- ✅ **Tag format**: `TAGS='"demo","key:value"'`
- ✅ **Cleanup**: Use provided cleanup script for tagged resources
