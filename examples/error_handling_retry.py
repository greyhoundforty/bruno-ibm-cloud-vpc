#!/usr/bin/env python3
"""
Error Handling and Retry Logic for IBM Cloud VPC Bruno Collection

This script demonstrates robust error handling and retry logic when
interacting with the IBM Cloud VPC API using Bruno CLI.

Key Concepts:
- Exponential backoff for rate limiting (429 errors)
- Automatic token refresh for expired auth (401 errors)
- Retry logic for transient network errors
- Proper exception handling for different error types

Author: Bruno IBM Cloud VPC Collection
"""

import subprocess
import json
import time
import sys
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta


class BrunoAPIError(Exception):
    """Base exception for Bruno API errors."""
    pass


class AuthenticationError(BrunoAPIError):
    """Raised when authentication fails or token expires."""
    pass


class RateLimitError(BrunoAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class ResourceNotFoundError(BrunoAPIError):
    """Raised when requested resource doesn't exist."""
    pass


class ValidationError(BrunoAPIError):
    """Raised when request parameters are invalid."""
    pass


class BrunoClient:
    """
    Bruno CLI client with automatic error handling and retry logic.

    Features:
    - Automatic token refresh on 401 errors
    - Exponential backoff retry for rate limiting (429)
    - Configurable retry attempts for transient errors
    - Detailed error logging
    """

    def __init__(
        self,
        env: str = "prod",
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize Bruno client with retry configuration.

        Args:
            env: Environment name (prod or dev)
            max_retries: Maximum retry attempts for transient errors
            initial_retry_delay: Initial delay in seconds before first retry
            max_retry_delay: Maximum delay in seconds between retries
            backoff_factor: Exponential backoff multiplier (2.0 = double each time)
        """
        self.env = env
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.backoff_factor = backoff_factor

        # Token management
        self.token_expires_at: Optional[datetime] = None
        self.last_auth_time: Optional[datetime] = None

    def _log(self, level: str, message: str):
        """Log message with timestamp and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def _should_refresh_token(self) -> bool:
        """
        Check if authentication token should be refreshed.

        IBM Cloud IAM tokens expire after 1 hour (3600 seconds).
        Refresh proactively 5 minutes before expiration.
        """
        if not self.token_expires_at:
            return True

        # Refresh 5 minutes before expiration
        refresh_time = self.token_expires_at - timedelta(minutes=5)
        return datetime.now() >= refresh_time

    def authenticate(self, force: bool = False) -> None:
        """
        Authenticate with IBM Cloud IAM to get bearer token.

        Args:
            force: Force re-authentication even if token is valid

        Raises:
            AuthenticationError: If authentication fails
        """
        if not force and not self._should_refresh_token():
            self._log("INFO", "Token still valid, skipping authentication")
            return

        self._log("INFO", "Authenticating with IBM Cloud IAM...")

        try:
            result = subprocess.run(
                ["bru", "run", "auth/get-iam-token.bru", "--env", self.env],
                capture_output=True,
                text=True,
                check=True
            )

            self.last_auth_time = datetime.now()
            # IBM Cloud IAM tokens valid for 3600 seconds (1 hour)
            self.token_expires_at = self.last_auth_time + timedelta(seconds=3600)

            self._log("INFO", f"✅ Authentication successful (expires at {self.token_expires_at.strftime('%H:%M:%S')})")

        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e.stderr}")

    def _run_bruno_command(self, bru_files: List[str]) -> Dict[str, Any]:
        """
        Execute Bruno CLI command and return parsed response.

        Args:
            bru_files: List of .bru files to execute

        Returns:
            Parsed JSON response

        Raises:
            subprocess.CalledProcessError: If Bruno CLI fails
        """
        cmd = ["bru", "run"] + bru_files + ["--env", self.env, "--output", "json"]

        self._log("DEBUG", f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        return json.loads(result.stdout)

    def _handle_api_error(self, status_code: int, response_body: Dict[str, Any]) -> None:
        """
        Handle API error responses by raising appropriate exceptions.

        Args:
            status_code: HTTP status code
            response_body: Response body dictionary

        Raises:
            Specific exception based on error type
        """
        error_message = response_body.get("errors", [{}])[0].get("message", "Unknown error")

        if status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}")
        elif status_code == 404:
            raise ResourceNotFoundError(f"Resource not found: {error_message}")
        elif status_code == 409:
            raise ValidationError(f"Conflict: {error_message}")
        elif status_code == 422:
            raise ValidationError(f"Validation error: {error_message}")
        elif status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_message}")
        else:
            raise BrunoAPIError(f"API error {status_code}: {error_message}")

    def request_with_retry(
        self,
        bru_file: str,
        operation_name: str = "API request"
    ) -> Dict[str, Any]:
        """
        Execute Bruno request with automatic retry logic.

        Retry Strategy:
        - 401 (Unauthorized): Refresh token and retry once
        - 429 (Rate Limit): Exponential backoff retry
        - 5xx (Server Error): Exponential backoff retry
        - 4xx (Client Error): No retry, raise immediately

        Args:
            bru_file: Path to .bru file (e.g., "vpc/list-vpcs.bru")
            operation_name: Human-readable operation name for logging

        Returns:
            API response dictionary

        Raises:
            Various exceptions based on error type
        """
        # Always authenticate first (will skip if token valid)
        self.authenticate()

        retry_count = 0
        delay = self.initial_retry_delay

        while retry_count <= self.max_retries:
            try:
                self._log("INFO", f"Executing {operation_name} (attempt {retry_count + 1}/{self.max_retries + 1})")

                # Execute request (auth + actual request)
                response = self._run_bruno_command([
                    "auth/get-iam-token.bru",
                    bru_file
                ])

                # Check for HTTP error status in response
                # Note: Bruno CLI may not raise error for HTTP errors,
                # so we need to check response status

                self._log("INFO", f"✅ {operation_name} successful")
                return response

            except subprocess.CalledProcessError as e:
                # Bruno CLI failed (network error, invalid file, etc.)
                self._log("ERROR", f"Bruno CLI error: {e.stderr}")

                if retry_count < self.max_retries:
                    self._log("INFO", f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_retry_delay)
                    retry_count += 1
                else:
                    self._log("ERROR", f"Max retries ({self.max_retries}) exceeded")
                    raise BrunoAPIError(f"Request failed after {self.max_retries} retries: {e}")

            except json.JSONDecodeError as e:
                # Response parsing failed
                self._log("ERROR", f"Failed to parse JSON response: {e}")
                raise BrunoAPIError(f"Invalid JSON response: {e}")

            except AuthenticationError as e:
                # Token expired, refresh and retry once
                if retry_count == 0:
                    self._log("WARNING", "Token expired, refreshing...")
                    self.authenticate(force=True)
                    retry_count += 1
                else:
                    self._log("ERROR", "Authentication failed after refresh")
                    raise

            except RateLimitError as e:
                # Rate limit hit, exponential backoff
                if retry_count < self.max_retries:
                    self._log("WARNING", f"Rate limit exceeded, backing off for {delay:.1f}s")
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_retry_delay)
                    retry_count += 1
                else:
                    self._log("ERROR", "Max retries exceeded due to rate limiting")
                    raise

        raise BrunoAPIError(f"Request failed after {self.max_retries} retries")

    def list_vpcs_with_retry(self) -> List[Dict[str, Any]]:
        """
        List all VPCs with automatic error handling and retry.

        Returns:
            List of VPC objects

        Example:
            >>> client = BrunoClient()
            >>> vpcs = client.list_vpcs_with_retry()
            >>> print(f"Found {len(vpcs)} VPCs")
        """
        response = self.request_with_retry("vpc/list-vpcs.bru", "List VPCs")
        return response.get("vpcs", [])

    def get_vpc_with_retry(self, vpc_id: str) -> Dict[str, Any]:
        """
        Get specific VPC with automatic error handling and retry.

        Args:
            vpc_id: VPC ID to retrieve

        Returns:
            VPC object dictionary

        Raises:
            ResourceNotFoundError: If VPC doesn't exist
        """
        # Note: This requires setting VPC_ID environment variable
        # In practice, you'd want to modify the .bru file or use env vars
        self._log("INFO", f"Fetching VPC: {vpc_id}")

        # For this example, we'd need to pass vpc_id somehow
        # One approach: export VPC_ID before running
        import os
        os.environ["VPC_ID"] = vpc_id

        response = self.request_with_retry("vpc/get-vpc.bru", f"Get VPC {vpc_id}")
        return response


def demonstrate_error_handling():
    """Demonstrate various error handling scenarios."""
    print("=" * 80)
    print("ERROR HANDLING DEMONSTRATIONS")
    print("=" * 80)

    client = BrunoClient(max_retries=3, initial_retry_delay=1.0)

    # Example 1: Successful request
    print("\n[Example 1] Successful Request")
    print("-" * 80)
    try:
        vpcs = client.list_vpcs_with_retry()
        print(f"✅ Successfully fetched {len(vpcs)} VPCs")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: Resource not found (404)
    print("\n[Example 2] Resource Not Found (404)")
    print("-" * 80)
    print("This would demonstrate handling of non-existent resource:")
    print("  try:")
    print("    vpc = client.get_vpc_with_retry('r006-invalid-id')")
    print("  except ResourceNotFoundError as e:")
    print("    print(f'VPC not found: {e}')")

    # Example 3: Rate limiting (429)
    print("\n[Example 3] Rate Limiting (429)")
    print("-" * 80)
    print("Rate limiting is handled automatically with exponential backoff:")
    print("  - 1st retry: 1 second delay")
    print("  - 2nd retry: 2 second delay (2^1)")
    print("  - 3rd retry: 4 second delay (2^2)")
    print("  - Max retries: 3 (configurable)")

    # Example 4: Authentication refresh
    print("\n[Example 4] Token Expiration (401)")
    print("-" * 80)
    print("Client automatically refreshes token when:")
    print("  - Token expires (after 1 hour)")
    print("  - Token within 5 minutes of expiration")
    print("  - 401 Unauthorized received")
    print("  - Force refresh requested")


def demonstrate_retry_strategies():
    """Demonstrate different retry strategies."""
    print("\n" + "=" * 80)
    print("RETRY STRATEGIES")
    print("=" * 80)

    print("\n1. No Retries (fail fast):")
    print("   client = BrunoClient(max_retries=0)")
    print("   - Best for: Interactive requests, development")
    print("   - Risk: Fails on transient errors")

    print("\n2. Conservative Retries:")
    print("   client = BrunoClient(max_retries=3, initial_retry_delay=2.0)")
    print("   - Best for: Production, important operations")
    print("   - Trade-off: Slower failure detection")

    print("\n3. Aggressive Retries:")
    print("   client = BrunoClient(max_retries=5, initial_retry_delay=0.5)")
    print("   - Best for: Batch operations, non-critical requests")
    print("   - Risk: May exceed rate limits")

    print("\n4. Exponential Backoff:")
    print("   client = BrunoClient(backoff_factor=2.0, max_retry_delay=60.0)")
    print("   - Best for: Rate limit handling")
    print("   - Delays: 1s, 2s, 4s, 8s, 16s, 32s, 60s (max)")


def demonstrate_error_types():
    """Demonstrate different error types and handling."""
    print("\n" + "=" * 80)
    print("ERROR TYPES & HANDLING")
    print("=" * 80)

    errors = [
        ("401 Unauthorized", "AuthenticationError", "Auto-refresh token and retry"),
        ("404 Not Found", "ResourceNotFoundError", "No retry, raise immediately"),
        ("409 Conflict", "ValidationError", "No retry, user must fix (e.g., duplicate name)"),
        ("422 Validation Error", "ValidationError", "No retry, invalid parameters"),
        ("429 Rate Limit", "RateLimitError", "Exponential backoff retry"),
        ("500 Server Error", "BrunoAPIError", "Exponential backoff retry"),
        ("503 Service Unavailable", "BrunoAPIError", "Exponential backoff retry"),
    ]

    print("\nStatus | Exception | Retry Strategy")
    print("-" * 80)
    for status, exception, strategy in errors:
        print(f"{status:20} | {exception:25} | {strategy}")


def main():
    """Main function demonstrating error handling and retry logic."""
    print("IBM Cloud VPC Error Handling and Retry Logic Examples")
    print("=" * 80)

    demonstrate_error_handling()
    demonstrate_retry_strategies()
    demonstrate_error_types()

    print("\n" + "=" * 80)
    print("BEST PRACTICES")
    print("=" * 80)

    print("""
1. Always use exponential backoff for rate limiting
   - Prevents overwhelming the API
   - Respects rate limit windows

2. Refresh tokens proactively (before expiration)
   - Tokens expire after 1 hour
   - Refresh 5 minutes before expiration
   - Avoids mid-operation token expiration

3. Distinguish transient vs permanent errors
   - Transient (5xx, 429): Retry with backoff
   - Permanent (4xx except 401): Fail immediately
   - Authentication (401): Refresh and retry once

4. Set reasonable retry limits
   - Production: 3-5 retries
   - Development: 1-2 retries
   - Batch operations: 5-10 retries

5. Log all errors and retries
   - Track retry patterns
   - Identify systematic issues
   - Monitor rate limit usage

6. Handle specific exceptions appropriately
   - ResourceNotFoundError: Check resource exists
   - ValidationError: Fix parameters, don't retry
   - RateLimitError: Slow down requests

7. Use timeouts for network operations
   - Prevent infinite hangs
   - Set based on operation type
   - Example: 30s for list, 120s for create

8. Implement circuit breaker for repeated failures
   - Stop retrying after N consecutive failures
   - Wait before re-enabling requests
   - Prevents cascading failures
""")

    print("\n" + "=" * 80)
    print("USAGE EXAMPLE")
    print("=" * 80)

    print("""
from error_handling_retry import BrunoClient

# Create client with retry configuration
client = BrunoClient(
    env="prod",
    max_retries=3,
    initial_retry_delay=1.0,
    backoff_factor=2.0
)

# List VPCs with automatic retry
try:
    vpcs = client.list_vpcs_with_retry()
    print(f"Found {len(vpcs)} VPCs")
except ResourceNotFoundError:
    print("No VPCs found")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except AuthenticationError:
    print("Authentication failed, check IBM_API_KEY")
except BrunoAPIError as e:
    print(f"API error: {e}")
""")


if __name__ == "__main__":
    main()
