#!/usr/bin/env python3
"""
Request Chaining Workflow for IBM Cloud VPC

This script demonstrates how to chain multiple Bruno requests together
to create a complete VPC infrastructure in one automated workflow:

Workflow: VPC → Subnet → Security Group → Security Rules → Instance → Floating IP

Each step depends on the previous step's output (IDs, names, etc.).
The script handles dependencies automatically and provides clear progress reporting.

Author: Bruno IBM Cloud VPC Collection
"""

import subprocess
import json
import sys
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime


class WorkflowStep:
    """Represents a single step in the workflow with dependencies."""

    def __init__(
        self,
        name: str,
        description: str,
        bru_file: str,
        env_vars: Dict[str, str],
        extract_id_key: Optional[str] = None
    ):
        """
        Initialize workflow step.

        Args:
            name: Step name (e.g., "create_vpc")
            description: Human-readable description
            bru_file: Bruno request file path
            env_vars: Environment variables to set for this request
            extract_id_key: JSON key path to extract ID from response (e.g., "id", "vpc.id")
        """
        self.name = name
        self.description = description
        self.bru_file = bru_file
        self.env_vars = env_vars
        self.extract_id_key = extract_id_key
        self.result: Optional[Dict[str, Any]] = None
        self.extracted_id: Optional[str] = None
        self.status: str = "pending"  # pending, running, completed, failed
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def duration(self) -> float:
        """Get step duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class VPCWorkflow:
    """
    Automated workflow for creating complete VPC infrastructure.

    Creates (in order):
    1. VPC
    2. Subnet
    3. Security Group
    4. Security Group Rules (SSH, HTTP, HTTPS, outbound)
    5. Virtual Server Instance
    6. Floating IP (optional)
    """

    def __init__(
        self,
        vpc_name: str,
        subnet_name: str,
        sg_name: str,
        instance_name: str,
        zone_name: str = "us-south-1",
        subnet_ip_count: int = 256,
        instance_profile: str = "cx2-2x4",
        image_id: Optional[str] = None,
        ssh_key_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        env: str = "prod",
        create_floating_ip: bool = True
    ):
        """
        Initialize VPC infrastructure workflow.

        Args:
            vpc_name: Name for new VPC
            subnet_name: Name for new subnet
            sg_name: Name for new security group
            instance_name: Name for new instance
            zone_name: Availability zone (default: us-south-1)
            subnet_ip_count: IPs in subnet (default: 256)
            instance_profile: Instance profile (default: cx2-2x4)
            image_id: OS image ID (required)
            ssh_key_id: SSH key ID (required for Linux)
            resource_group_id: Resource group ID (optional)
            env: Bruno environment (prod or dev)
            create_floating_ip: Create floating IP for external access
        """
        self.vpc_name = vpc_name
        self.subnet_name = subnet_name
        self.sg_name = sg_name
        self.instance_name = instance_name
        self.zone_name = zone_name
        self.subnet_ip_count = subnet_ip_count
        self.instance_profile = instance_profile
        self.image_id = image_id
        self.ssh_key_id = ssh_key_id
        self.resource_group_id = resource_group_id
        self.env = env
        self.create_floating_ip = create_floating_ip

        # Workflow state
        self.steps: List[WorkflowStep] = []
        self.current_step_index = 0
        self.workflow_status = "not_started"  # not_started, running, completed, failed
        self.workflow_start_time: Optional[datetime] = None
        self.workflow_end_time: Optional[datetime] = None

        # Resource IDs (populated as workflow progresses)
        self.vpc_id: Optional[str] = None
        self.subnet_id: Optional[str] = None
        self.sg_id: Optional[str] = None
        self.instance_id: Optional[str] = None
        self.floating_ip_id: Optional[str] = None
        self.floating_ip_address: Optional[str] = None

    def _log(self, level: str, message: str):
        """Log message with timestamp and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def _run_bruno_request(
        self,
        bru_file: str,
        env_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Execute Bruno CLI request with environment variables.

        Args:
            bru_file: Path to .bru file
            env_vars: Environment variables to set

        Returns:
            Parsed JSON response

        Raises:
            subprocess.CalledProcessError: If request fails
        """
        # Merge with existing environment
        env = os.environ.copy()
        env.update(env_vars)

        cmd = [
            "bru", "run",
            "auth/get-iam-token.bru",  # Always authenticate first
            bru_file,
            "--env", self.env,
            "--output", "json"
        ]

        self._log("DEBUG", f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        return json.loads(result.stdout)

    def _extract_value(self, data: Dict[str, Any], key_path: str) -> Optional[str]:
        """
        Extract value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key_path: Dot-separated key path (e.g., "vpc.id", "primary_network_interface.id")

        Returns:
            Extracted value or None

        Example:
            >>> data = {"vpc": {"id": "r006-abc123"}}
            >>> _extract_value(data, "vpc.id")
            "r006-abc123"
        """
        keys = key_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return str(current) if current is not None else None

    def _build_steps(self):
        """Build workflow steps based on configuration."""
        self.steps = []

        # Step 1: Create VPC
        env_vars = {
            "NEW_VPC_NAME": self.vpc_name,
        }
        if self.resource_group_id:
            env_vars["RESOURCE_GROUP_ID"] = self.resource_group_id

        self.steps.append(WorkflowStep(
            name="create_vpc",
            description=f"Create VPC '{self.vpc_name}'",
            bru_file="vpc/create-vpc.bru",
            env_vars=env_vars,
            extract_id_key="id"
        ))

        # Step 2: Create Subnet
        self.steps.append(WorkflowStep(
            name="create_subnet",
            description=f"Create subnet '{self.subnet_name}' in zone {self.zone_name}",
            bru_file="vpc/subnets/create-subnet.bru",
            env_vars={
                "NEW_SUBNET_NAME": self.subnet_name,
                "VPC_ID": "${vpc_id}",  # Placeholder, replaced at runtime
                "ZONE_NAME": self.zone_name,
                "SUBNET_IP_COUNT": str(self.subnet_ip_count)
            },
            extract_id_key="id"
        ))

        # Step 3: Create Security Group
        self.steps.append(WorkflowStep(
            name="create_security_group",
            description=f"Create security group '{self.sg_name}'",
            bru_file="vpc/security-groups/create-security-group.bru",
            env_vars={
                "NEW_SG_NAME": self.sg_name,
                "VPC_ID": "${vpc_id}"
            },
            extract_id_key="id"
        ))

        # Step 4: Add SSH rule
        self.steps.append(WorkflowStep(
            name="add_ssh_rule",
            description="Add SSH inbound rule (port 22)",
            bru_file="vpc/security-groups/add-rule-ssh.bru",
            env_vars={
                "SECURITY_GROUP_ID": "${sg_id}",
                "SSH_SOURCE_CIDR": "0.0.0.0/0"  # Allow from anywhere (adjust as needed)
            },
            extract_id_key="id"
        ))

        # Step 5: Add HTTP rule
        self.steps.append(WorkflowStep(
            name="add_http_rule",
            description="Add HTTP inbound rule (port 80)",
            bru_file="vpc/security-groups/add-rule-http.bru",
            env_vars={
                "SECURITY_GROUP_ID": "${sg_id}"
            },
            extract_id_key="id"
        ))

        # Step 6: Add HTTPS rule
        self.steps.append(WorkflowStep(
            name="add_https_rule",
            description="Add HTTPS inbound rule (port 443)",
            bru_file="vpc/security-groups/add-rule-https.bru",
            env_vars={
                "SECURITY_GROUP_ID": "${sg_id}"
            },
            extract_id_key="id"
        ))

        # Step 7: Add outbound all rule
        self.steps.append(WorkflowStep(
            name="add_outbound_rule",
            description="Add outbound all rule",
            bru_file="vpc/security-groups/add-rule-outbound-all.bru",
            env_vars={
                "SECURITY_GROUP_ID": "${sg_id}"
            },
            extract_id_key="id"
        ))

        # Step 8: Create Instance
        if not self.image_id:
            raise ValueError("image_id is required. Run 'mise run instances:list-images' to find an image ID")
        if not self.ssh_key_id:
            raise ValueError("ssh_key_id is required for Linux instances. Run 'mise run ssh-keys:list' to find an SSH key ID")

        self.steps.append(WorkflowStep(
            name="create_instance",
            description=f"Create instance '{self.instance_name}' with profile {self.instance_profile}",
            bru_file="vpc/instances/create-instance.bru",
            env_vars={
                "NEW_INSTANCE_NAME": self.instance_name,
                "VPC_ID": "${vpc_id}",
                "ZONE_NAME": self.zone_name,
                "PROFILE_NAME": self.instance_profile,
                "IMAGE_ID": self.image_id,
                "SUBNET_ID": "${subnet_id}",
                "SECURITY_GROUP_ID": "${sg_id}",
                "SSH_KEY_ID": self.ssh_key_id
            },
            extract_id_key="id"
        ))

        # Step 9: Create Floating IP (optional)
        if self.create_floating_ip:
            self.steps.append(WorkflowStep(
                name="create_floating_ip",
                description=f"Create floating IP for external access",
                bru_file="vpc/floating-ips/create-floating-ip.bru",
                env_vars={
                    "NEW_FIP_NAME": f"{self.instance_name}-fip",
                    "ZONE_NAME": self.zone_name
                },
                extract_id_key="id"
            ))

    def _resolve_placeholders(self, env_vars: Dict[str, str]) -> Dict[str, str]:
        """
        Replace placeholder variables with actual values from previous steps.

        Args:
            env_vars: Environment variables with placeholders

        Returns:
            Environment variables with resolved values
        """
        resolved = {}
        for key, value in env_vars.items():
            if value == "${vpc_id}" and self.vpc_id:
                resolved[key] = self.vpc_id
            elif value == "${subnet_id}" and self.subnet_id:
                resolved[key] = self.subnet_id
            elif value == "${sg_id}" and self.sg_id:
                resolved[key] = self.sg_id
            elif value == "${instance_id}" and self.instance_id:
                resolved[key] = self.instance_id
            else:
                resolved[key] = value
        return resolved

    def execute_step(self, step: WorkflowStep) -> bool:
        """
        Execute a single workflow step.

        Args:
            step: Workflow step to execute

        Returns:
            True if successful, False otherwise
        """
        step.status = "running"
        step.start_time = datetime.now()

        self._log("INFO", f"▶ {step.description}")

        try:
            # Resolve placeholder variables
            env_vars = self._resolve_placeholders(step.env_vars)

            # Execute request
            response = self._run_bruno_request(step.bru_file, env_vars)

            # Store result
            step.result = response
            step.status = "completed"
            step.end_time = datetime.now()

            # Extract ID if specified
            if step.extract_id_key:
                extracted_id = self._extract_value(response, step.extract_id_key)
                if extracted_id:
                    step.extracted_id = extracted_id

                    # Store in workflow state
                    if step.name == "create_vpc":
                        self.vpc_id = extracted_id
                        self._log("INFO", f"  ✅ VPC created: {self.vpc_id}")
                    elif step.name == "create_subnet":
                        self.subnet_id = extracted_id
                        self._log("INFO", f"  ✅ Subnet created: {self.subnet_id}")
                    elif step.name == "create_security_group":
                        self.sg_id = extracted_id
                        self._log("INFO", f"  ✅ Security group created: {self.sg_id}")
                    elif step.name == "create_instance":
                        self.instance_id = extracted_id
                        self._log("INFO", f"  ✅ Instance created: {self.instance_id}")
                    elif step.name == "create_floating_ip":
                        self.floating_ip_id = extracted_id
                        # Also extract IP address
                        self.floating_ip_address = self._extract_value(response, "address")
                        self._log("INFO", f"  ✅ Floating IP created: {self.floating_ip_address} ({self.floating_ip_id})")
                    else:
                        self._log("INFO", f"  ✅ Rule created: {extracted_id}")

            self._log("INFO", f"  ✅ Completed in {step.duration():.1f}s")
            return True

        except subprocess.CalledProcessError as e:
            step.status = "failed"
            step.error = str(e.stderr)
            step.end_time = datetime.now()
            self._log("ERROR", f"  ❌ Failed: {e.stderr}")
            return False

        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.end_time = datetime.now()
            self._log("ERROR", f"  ❌ Failed: {e}")
            return False

    def execute(self) -> bool:
        """
        Execute complete workflow.

        Returns:
            True if all steps successful, False otherwise
        """
        self._log("INFO", "=" * 80)
        self._log("INFO", "STARTING VPC INFRASTRUCTURE WORKFLOW")
        self._log("INFO", "=" * 80)

        self.workflow_status = "running"
        self.workflow_start_time = datetime.now()

        # Build steps
        try:
            self._build_steps()
        except ValueError as e:
            self._log("ERROR", f"Configuration error: {e}")
            self.workflow_status = "failed"
            return False

        self._log("INFO", f"Total steps: {len(self.steps)}")
        self._log("INFO", "")

        # Execute steps sequentially
        for i, step in enumerate(self.steps, 1):
            self.current_step_index = i
            self._log("INFO", f"[Step {i}/{len(self.steps)}]")

            success = self.execute_step(step)

            if not success:
                self.workflow_status = "failed"
                self.workflow_end_time = datetime.now()
                self._print_summary()
                return False

            # Small delay between steps for API rate limiting
            if i < len(self.steps):
                time.sleep(1)

        self.workflow_status = "completed"
        self.workflow_end_time = datetime.now()
        self._print_summary()
        return True

    def _print_summary(self):
        """Print workflow execution summary."""
        self._log("INFO", "")
        self._log("INFO", "=" * 80)
        self._log("INFO", "WORKFLOW SUMMARY")
        self._log("INFO", "=" * 80)

        total_duration = 0.0
        if self.workflow_start_time and self.workflow_end_time:
            total_duration = (self.workflow_end_time - self.workflow_start_time).total_seconds()

        print(f"\nStatus: {self.workflow_status.upper()}")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"\nSteps Completed: {sum(1 for s in self.steps if s.status == 'completed')}/{len(self.steps)}")

        print("\n--- Step Results ---")
        for i, step in enumerate(self.steps, 1):
            status_icon = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏸"
            print(f"{i}. {status_icon} {step.description} ({step.duration():.1f}s)")
            if step.extracted_id:
                print(f"   ID: {step.extracted_id}")
            if step.error:
                print(f"   Error: {step.error}")

        if self.workflow_status == "completed":
            print("\n--- Created Resources ---")
            print(f"VPC ID: {self.vpc_id}")
            print(f"Subnet ID: {self.subnet_id}")
            print(f"Security Group ID: {self.sg_id}")
            print(f"Instance ID: {self.instance_id}")
            if self.floating_ip_id:
                print(f"Floating IP: {self.floating_ip_address} ({self.floating_ip_id})")

            print("\n--- Next Steps ---")
            print("1. Wait for instance to reach 'running' status (3-5 minutes):")
            print(f"   watch -n 10 \"INSTANCE_ID={self.instance_id} mise run instances:get\"")

            if self.floating_ip_address:
                print("\n2. Connect via SSH:")
                print(f"   ssh root@{self.floating_ip_address}")
                print(f"   ssh ubuntu@{self.floating_ip_address}  # For Ubuntu images")

            print("\n3. Clean up resources when done:")
            print(f"   INSTANCE_ID={self.instance_id} mise run instances:delete")
            if self.floating_ip_id:
                print(f"   FLOATING_IP_ID={self.floating_ip_id} mise run floating-ips:delete")
            print(f"   SUBNET_ID={self.subnet_id} mise run subnets:delete")
            print(f"   SECURITY_GROUP_ID={self.sg_id} mise run security-groups:delete")
            print(f"   VPC_ID={self.vpc_id} mise run vpc:delete")


def main():
    """Main function demonstrating workflow usage."""
    print("IBM Cloud VPC Workflow Chaining Example")
    print("=" * 80)

    # Example configuration (would typically come from CLI args or config file)
    config = {
        "vpc_name": "demo-vpc",
        "subnet_name": "demo-subnet",
        "sg_name": "demo-sg",
        "instance_name": "demo-instance",
        "zone_name": "us-south-1",
        "subnet_ip_count": 256,
        "instance_profile": "cx2-2x4",
        "image_id": None,  # REQUIRED: Get from 'mise run instances:list-images'
        "ssh_key_id": None,  # REQUIRED: Get from 'mise run ssh-keys:list'
        "resource_group_id": None,  # Optional
        "create_floating_ip": True
    }

    print("\n⚠️  Configuration Required:")
    print("Before running this workflow, you need to:")
    print("1. Get an image ID: mise run instances:list-images")
    print("2. Get an SSH key ID: mise run ssh-keys:list")
    print("3. Update this script with those values")
    print("\nExample usage:")
    print("""
workflow = VPCWorkflow(
    vpc_name="my-vpc",
    subnet_name="my-subnet",
    sg_name="my-sg",
    instance_name="my-instance",
    zone_name="us-south-1",
    image_id="r006-abc123...",  # Ubuntu 22.04 LTS
    ssh_key_id="r006-def456...",  # Your SSH key
    instance_profile="cx2-2x4"
)

success = workflow.execute()
if success:
    print(f"Infrastructure created! Instance: {workflow.instance_id}")
else:
    print("Workflow failed. Check logs above.")
""")


if __name__ == "__main__":
    main()
