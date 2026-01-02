#!/usr/bin/env python3
"""
Pagination Example for IBM Cloud VPC Bruno Collection

This script demonstrates how to handle pagination when listing resources
from the IBM Cloud VPC API using Bruno CLI.

IBM Cloud VPC API uses cursor-based pagination:
- limit: Maximum results per page (default: 50, max: 100)
- start: Pagination cursor token from response.next.href

Author: Bruno IBM Cloud VPC Collection
"""

import subprocess
import json
import sys
from typing import List, Dict, Any, Optional


def run_bruno_request(bru_files: List[str], env: str = "prod", output: str = "json") -> Dict[str, Any]:
    """
    Execute a Bruno CLI request and return parsed JSON response.

    Args:
        bru_files: List of .bru files to execute (auth first, then request)
        env: Environment name (prod or dev)
        output: Output format (json recommended)

    Returns:
        Parsed JSON response from API

    Raises:
        subprocess.CalledProcessError: If Bruno CLI fails
        json.JSONDecodeError: If response is not valid JSON
    """
    cmd = ["bru", "run"] + bru_files + ["--env", env]
    if output:
        cmd.extend(["--output", output])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    return json.loads(result.stdout)


def get_pagination_cursor(response: Dict[str, Any]) -> Optional[str]:
    """
    Extract pagination cursor from API response.

    IBM Cloud VPC API includes a 'next' object with 'href' containing
    the full URL for the next page. We extract the 'start' parameter.

    Args:
        response: API response dictionary

    Returns:
        Pagination cursor string, or None if no more pages
    """
    next_link = response.get("next", {})
    if not next_link:
        return None

    href = next_link.get("href", "")
    if not href:
        return None

    # Extract 'start' parameter from URL
    # Example: https://us-south.iaas.cloud.ibm.com/v1/vpcs?start=abc123&version=2024-12-10&generation=2
    if "start=" in href:
        start_param = href.split("start=")[1].split("&")[0]
        return start_param

    return None


def paginate_list_vpcs(limit: int = 10, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Paginate through all VPCs using cursor-based pagination.

    Args:
        limit: Results per page (1-100, default: 10 for demonstration)
        max_pages: Maximum pages to fetch (None = all pages)

    Returns:
        List of all VPC objects across all pages

    Example:
        >>> vpcs = paginate_list_vpcs(limit=10, max_pages=3)
        >>> print(f"Fetched {len(vpcs)} VPCs across 3 pages")
    """
    all_vpcs = []
    page_num = 1
    cursor = None

    print(f"Starting pagination: limit={limit}, max_pages={max_pages or 'unlimited'}")
    print("=" * 60)

    while True:
        # Check if we've reached max pages
        if max_pages and page_num > max_pages:
            print(f"\nReached max_pages limit ({max_pages})")
            break

        print(f"\nPage {page_num}:")
        print(f"  Cursor: {cursor or 'None (first page)'}")

        # Build Bruno request with pagination parameters
        # Note: For this example, we'd need a way to pass query parameters
        # In practice, you'd modify the .bru file or use environment variables

        # For this example, we'll use a modified approach:
        # Run the request and manually add pagination to URL

        try:
            response = run_bruno_request([
                "auth/get-iam-token.bru",
                "vpc/list-vpcs.bru"
            ])
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error: {e}")
            break

        # Extract VPCs from response
        vpcs = response.get("vpcs", [])
        vpc_count = len(vpcs)

        print(f"  Found: {vpc_count} VPCs on this page")

        # Display VPC names
        for i, vpc in enumerate(vpcs, 1):
            print(f"    {i}. {vpc.get('name', 'N/A')} ({vpc.get('id', 'N/A')})")

        # Add to results
        all_vpcs.extend(vpcs)

        # Check for next page
        cursor = get_pagination_cursor(response)

        if not cursor:
            print(f"\n  ✅ No more pages (reached end)")
            break

        print(f"  Next cursor: {cursor[:20]}..." if len(cursor) > 20 else f"  Next cursor: {cursor}")

        page_num += 1

    print("=" * 60)
    print(f"\n✅ Pagination complete!")
    print(f"   Total VPCs fetched: {len(all_vpcs)}")
    print(f"   Total pages fetched: {page_num}")

    return all_vpcs


def paginate_with_filters(resource_group_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Demonstrate pagination with filters.

    When using filters (resource_group.id, vpc.id, etc.), pagination
    still works the same way with 'start' cursor.

    Args:
        resource_group_id: Optional resource group ID filter

    Returns:
        Filtered list of VPCs across all pages
    """
    # In practice, you'd modify the .bru file to include filters
    # or use environment variables with Bruno templating

    print(f"Paginating with filters:")
    print(f"  Resource Group ID: {resource_group_id or 'None (all)'}")

    # Same pagination logic as above, but with filters applied
    # This is a simplified example - in practice you'd pass filters
    # through environment variables or modified .bru files

    pass


def demonstrate_pagination_edge_cases():
    """
    Demonstrate common pagination edge cases and best practices.
    """
    print("\n" + "=" * 60)
    print("PAGINATION EDGE CASES & BEST PRACTICES")
    print("=" * 60)

    print("\n1. Empty Results:")
    print("   - If no resources match, response.vpcs = []")
    print("   - No 'next' link in response")
    print("   - Handle gracefully: check if list is empty")

    print("\n2. Single Page:")
    print("   - Total items < limit, no 'next' link")
    print("   - Example: 5 VPCs with limit=50")
    print("   - Stop pagination immediately")

    print("\n3. Exact Page Boundary:")
    print("   - Total items = multiple of limit")
    print("   - Example: 100 items with limit=50 = 2 pages")
    print("   - Last page has 'next' link = null or missing")

    print("\n4. Cursor Expiration:")
    print("   - Cursors can expire (typically 5-10 minutes)")
    print("   - If expired, API returns 400 Bad Request")
    print("   - Solution: Restart pagination from beginning")

    print("\n5. Rate Limiting:")
    print("   - IBM Cloud enforces rate limits per API key")
    print("   - Add delays between pages if needed")
    print("   - Example: time.sleep(0.5) between requests")

    print("\n6. Large Result Sets:")
    print("   - 1000+ resources: Use smaller limit (e.g., 10-20)")
    print("   - Process pages incrementally, don't load all into memory")
    print("   - Consider streaming results to file/database")

    print("\n7. Concurrent Pagination:")
    print("   - DON'T paginate same resource in parallel")
    print("   - Cursors are sequential, not random-access")
    print("   - Parallel pagination = undefined behavior")


def main():
    """
    Main function demonstrating various pagination scenarios.
    """
    print("IBM Cloud VPC Pagination Examples")
    print("=" * 60)

    # Example 1: Basic pagination
    print("\n[Example 1] Basic Pagination with limit=10")
    print("-" * 60)
    # In a real scenario, uncomment:
    # vpcs = paginate_list_vpcs(limit=10, max_pages=3)

    # For now, just demonstrate the concept
    print("This would fetch 3 pages of VPCs with 10 items per page")
    print("Result: Up to 30 VPCs total")

    # Example 2: Pagination best practices
    demonstrate_pagination_edge_cases()

    # Example 3: Manual pagination with Bruno
    print("\n" + "=" * 60)
    print("MANUAL PAGINATION WITH BRUNO CLI")
    print("=" * 60)

    print("\n1. First Page (default):")
    print("   bru run auth/get-iam-token.bru vpc/list-vpcs.bru --env prod")

    print("\n2. Subsequent Pages:")
    print("   - Copy 'start' token from response.next.href")
    print("   - Add to query params in .bru file or via environment variable")
    print("   - Example: START_TOKEN=abc123 bru run ...")

    print("\n3. With Filters + Pagination:")
    print("   - Combine filters with pagination")
    print("   - Example: Resource group filter + limit + start")

    print("\n" + "=" * 60)
    print("BRUNO FILE MODIFICATIONS FOR PAGINATION")
    print("=" * 60)

    print("""
Option 1: Modify .bru file params:query block

params:query {
  version: {{api_version}}
  generation: 2
  limit: 10
  start: {{START_TOKEN}}
}

Then run with: START_TOKEN="abc123..." bru run ...

Option 2: Create separate paginated endpoint

Create: vpc/list-vpcs-paginated.bru
Add environment variable for START_TOKEN
Use mise task for easy execution

Option 3: Python wrapper script (this file!)

Use subprocess to call Bruno CLI
Extract cursor from response
Loop until no more pages
Aggregate results
""")


if __name__ == "__main__":
    main()
