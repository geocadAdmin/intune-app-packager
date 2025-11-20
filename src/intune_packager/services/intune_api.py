"""
Microsoft Graph API Client for Intune
Handles all interactions with Microsoft Intune via Graph API.
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

import aiohttp
from msal import PublicClientApplication, ConfidentialClientApplication

logger = logging.getLogger(__name__)


class IntuneAPIClient:
    """Client for Microsoft Graph API - Intune operations."""
    
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    GRAPH_API_BETA = "https://graph.microsoft.com/beta"
    
    # Required scopes
    SCOPES = [
        "DeviceManagementApps.ReadWrite.All",
        "Group.Read.All",
        "DeviceManagementManagedDevices.Read.All"
    ]
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Initialize Intune API client.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
        """
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        
        self.access_token = None
        self.token_cache_path = Path.home() / ".intune_packager" / "token_cache.json"
        
        logger.info("IntuneAPIClient initialized")
    
    async def authenticate_interactive(self) -> bool:
        """
        Authenticate using interactive browser flow (for GUI users).
        
        Returns:
            True if authentication successful
        """
        logger.info("Starting interactive authentication")
        
        if not self.client_id:
            raise ValueError("client_id is required for authentication")
        
        app = PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id or 'common'}"
        )
        
        # Try to get token from cache first
        accounts = app.get_accounts()
        if accounts:
            logger.info(f"Found {len(accounts)} cached account(s)")
            result = app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("Acquired token from cache")
                return True
        
        # Interactive authentication
        result = app.acquire_token_interactive(scopes=self.SCOPES)
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("Interactive authentication successful")
            return True
        else:
            error = result.get("error_description", "Unknown error")
            logger.error(f"Authentication failed: {error}")
            return False
    
    async def authenticate_service_principal(self, client_secret: str) -> bool:
        """
        Authenticate using service principal (for automation).
        
        Args:
            client_secret: Client secret for the service principal
            
        Returns:
            True if authentication successful
        """
        logger.info("Starting service principal authentication")
        
        if not all([self.tenant_id, self.client_id, client_secret]):
            raise ValueError("tenant_id, client_id, and client_secret are required")
        
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            logger.info("Service principal authentication successful")
            return True
        else:
            error = result.get("error_description", "Unknown error")
            logger.error(f"Authentication failed: {error}")
            return False
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_beta: bool = False
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Graph API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body (for POST/PATCH)
            params: Query parameters
            use_beta: Use beta endpoint instead of v1.0
            
        Returns:
            Response JSON
        """
        if not self.access_token:
            raise RuntimeError("Not authenticated. Call authenticate_* first.")
        
        base_url = self.GRAPH_API_BETA if use_beta else self.GRAPH_API_ENDPOINT
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise RuntimeError(f"API request failed: {response.status} - {error_text}")
                
                return await response.json()
    
    # ===== Azure AD Groups =====
    
    async def list_groups(self, search_query: Optional[str] = None) -> List[Dict]:
        """
        List Azure AD groups.
        
        Args:
            search_query: Optional search filter
            
        Returns:
            List of group objects
        """
        logger.info(f"Listing groups (search: {search_query})")
        
        params = {}
        if search_query:
            params["$filter"] = f"startswith(displayName,'{search_query}')"
        
        response = await self._make_request("GET", "groups", params=params)
        groups = response.get("value", [])
        
        logger.info(f"Found {len(groups)} groups")
        return groups
    
    async def get_group_by_name(self, group_name: str) -> Optional[Dict]:
        """
        Get a specific group by display name.
        
        Args:
            group_name: Display name of the group
            
        Returns:
            Group object or None if not found
        """
        params = {"$filter": f"displayName eq '{group_name}'"}
        response = await self._make_request("GET", "groups", params=params)
        
        groups = response.get("value", [])
        return groups[0] if groups else None
    
    # ===== Win32 App Management =====
    
    async def create_win32_app(self, app_metadata: Dict) -> Dict:
        """
        Create a Win32 app in Intune.
        
        Args:
            app_metadata: Application metadata
            
        Returns:
            Created app object with ID
        """
        logger.info(f"Creating Win32 app: {app_metadata.get('displayName')}")
        
        # Construct Win32 app payload
        payload = {
            "@odata.type": "#microsoft.graph.win32LobApp",
            "displayName": app_metadata["displayName"],
            "description": app_metadata.get("description", ""),
            "publisher": app_metadata.get("publisher", ""),
            "fileName": app_metadata["fileName"],
            "installCommandLine": app_metadata["installCommandLine"],
            "uninstallCommandLine": app_metadata["uninstallCommandLine"],
            "installExperience": {
                "runAsAccount": "system",
                "deviceRestartBehavior": app_metadata.get("deviceRestartBehavior", "basedOnReturnCode")
            },
            "detectionRules": app_metadata["detectionRules"],
            "requirementRules": app_metadata.get("requirementRules", []),
            "returnCodes": app_metadata.get("returnCodes", self._get_default_return_codes())
        }
        
        response = await self._make_request(
            "POST",
            "deviceAppManagement/mobileApps",
            data=payload,
            use_beta=True
        )
        
        app_id = response["id"]
        logger.info(f"Win32 app created with ID: {app_id}")
        
        return response
    
    async def upload_intunewin_content(self, app_id: str, intunewin_path: str) -> bool:
        """
        Upload .intunewin file content to Azure Storage.
        
        This is a complex multi-step process:
        1. Create content version
        2. Create file upload session
        3. Upload encrypted file to Azure Storage
        4. Commit the file
        
        Args:
            app_id: Application ID from create_win32_app
            intunewin_path: Path to .intunewin file
            
        Returns:
            True if upload successful
        """
        logger.info(f"Uploading .intunewin content for app {app_id}")
        
        file_size = os.path.getsize(intunewin_path)
        file_name = os.path.basename(intunewin_path)
        
        # Step 1: Create content version
        logger.info("Step 1: Creating content version")
        content_version_payload = {
            "@odata.type": "#microsoft.graph.mobileAppContent"
        }
        
        content_response = await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/microsoft.graph.win32LobApp/contentVersions",
            data=content_version_payload,
            use_beta=True
        )
        
        content_version_id = content_response["id"]
        logger.info(f"Content version created: {content_version_id}")
        
        # Step 2: Create file upload session
        logger.info("Step 2: Creating file upload session")
        file_payload = {
            "@odata.type": "#microsoft.graph.mobileAppContentFile",
            "name": file_name,
            "size": file_size,
            "sizeEncrypted": file_size,  # Simplified - actual encryption would change size
            "manifest": None
        }
        
        file_response = await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/microsoft.graph.win32LobApp/contentVersions/{content_version_id}/files",
            data=file_payload,
            use_beta=True
        )
        
        file_id = file_response["id"]
        logger.info(f"File entry created: {file_id}")
        
        # Step 3: Wait for Azure Storage URL
        logger.info("Step 3: Waiting for upload URL")
        max_retries = 30
        for i in range(max_retries):
            await asyncio.sleep(2)
            
            file_status = await self._make_request(
                "GET",
                f"deviceAppManagement/mobileApps/{app_id}/microsoft.graph.win32LobApp/contentVersions/{content_version_id}/files/{file_id}",
                use_beta=True
            )
            
            upload_state = file_status.get("uploadState")
            if upload_state == "azureStorageUriRequestSuccess":
                azure_storage_uri = file_status["azureStorageUri"]
                logger.info("Azure Storage URI received")
                break
        else:
            raise RuntimeError("Timeout waiting for Azure Storage URI")
        
        # Step 4: Upload to Azure Storage
        logger.info("Step 4: Uploading file to Azure Storage")
        await self._upload_to_azure_storage(azure_storage_uri, intunewin_path)
        
        # Step 5: Commit the file
        logger.info("Step 5: Committing file")
        commit_payload = {
            "fileEncryptionInfo": {
                "encryptionKey": "dummy_key",  # In real implementation, use actual encryption
                "macKey": "dummy_mac",
                "initializationVector": "dummy_iv",
                "mac": "dummy_mac_value",
                "profileIdentifier": "ProfileVersion1",
                "fileDigest": "dummy_digest",
                "fileDigestAlgorithm": "SHA256"
            }
        }
        
        await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/microsoft.graph.win32LobApp/contentVersions/{content_version_id}/files/{file_id}/commit",
            data=commit_payload,
            use_beta=True
        )
        
        logger.info("Upload completed successfully")
        return True
    
    async def _upload_to_azure_storage(self, sas_uri: str, file_path: str):
        """Upload file to Azure Storage using SAS URI."""
        # This is a simplified version - real implementation would use Azure SDK
        logger.info(f"Uploading {file_path} to Azure Storage")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        headers = {
            "x-ms-blob-type": "BlockBlob"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.put(sas_uri, data=file_data, headers=headers) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Azure Storage upload failed: {response.status}")
        
        logger.info("File uploaded to Azure Storage")
    
    # ===== App Assignments =====
    
    async def assign_app_to_groups(
        self,
        app_id: str,
        assignments: List[Dict]
    ) -> bool:
        """
        Assign app to Azure AD groups.
        
        Args:
            app_id: Application ID
            assignments: List of assignment configurations
            
        Example assignment:
            {
                "target": {
                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                    "groupId": "group-id-here"
                },
                "intent": "available",  # or "required" or "uninstall"
                "settings": {
                    "@odata.type": "#microsoft.graph.win32LobAppAssignmentSettings",
                    "notifications": "showAll",
                    "installTimeSettings": None,
                    "restartSettings": None
                }
            }
            
        Returns:
            True if assignments successful
        """
        logger.info(f"Assigning app {app_id} to {len(assignments)} groups")
        
        # Build assignment payload
        assignment_payload = {
            "mobileAppAssignments": []
        }
        
        for assignment in assignments:
            assignment_payload["mobileAppAssignments"].append({
                "@odata.type": "#microsoft.graph.mobileAppAssignment",
                "intent": assignment["intent"],
                "target": assignment["target"],
                "settings": assignment.get("settings", {
                    "@odata.type": "#microsoft.graph.win32LobAppAssignmentSettings",
                    "notifications": "showAll"
                })
            })
        
        await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/assign",
            data=assignment_payload,
            use_beta=True
        )
        
        logger.info("App assignments created successfully")
        return True
    
    # ===== Dependencies & Supersedence =====
    
    async def set_app_dependencies(
        self,
        app_id: str,
        dependency_app_ids: List[str]
    ) -> bool:
        """
        Set app dependencies (apps that must be installed first).
        
        Args:
            app_id: Application ID
            dependency_app_ids: List of app IDs that are dependencies
            
        Returns:
            True if dependencies set successfully
        """
        logger.info(f"Setting {len(dependency_app_ids)} dependencies for app {app_id}")
        
        relationships = []
        for dep_id in dependency_app_ids:
            relationships.append({
                "@odata.type": "#microsoft.graph.mobileAppDependency",
                "targetId": dep_id,
                "dependencyType": "autoInstall"
            })
        
        payload = {"relationships": relationships}
        
        await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/relationships",
            data=payload,
            use_beta=True
        )
        
        logger.info("Dependencies set successfully")
        return True
    
    async def set_app_supersedence(
        self,
        app_id: str,
        superseded_app_ids: List[str],
        uninstall_previous: bool = True
    ) -> bool:
        """
        Set app supersedence (replace old versions).
        
        Args:
            app_id: New application ID
            superseded_app_ids: List of old app IDs to replace
            uninstall_previous: Whether to uninstall superseded apps
            
        Returns:
            True if supersedence set successfully
        """
        logger.info(f"Setting supersedence for app {app_id}")
        
        relationships = []
        for old_app_id in superseded_app_ids:
            relationships.append({
                "@odata.type": "#microsoft.graph.mobileAppSupersedence",
                "targetId": old_app_id,
                "supersedenceType": "replace" if uninstall_previous else "update"
            })
        
        payload = {"relationships": relationships}
        
        await self._make_request(
            "POST",
            f"deviceAppManagement/mobileApps/{app_id}/relationships",
            data=payload,
            use_beta=True
        )
        
        logger.info("Supersedence set successfully")
        return True
    
    # ===== Deployment Monitoring =====
    
    async def get_app_install_status(self, app_id: str) -> Dict:
        """
        Get installation status for an app across all devices.
        
        Args:
            app_id: Application ID
            
        Returns:
            Installation status summary
        """
        logger.info(f"Getting install status for app {app_id}")
        
        response = await self._make_request(
            "GET",
            f"deviceAppManagement/mobileApps/{app_id}/deviceStatuses",
            use_beta=True
        )
        
        statuses = response.get("value", [])
        
        # Aggregate statistics
        summary = {
            "total_devices": len(statuses),
            "installed": 0,
            "failed": 0,
            "pending": 0,
            "not_applicable": 0,
            "devices": []
        }
        
        for status in statuses:
            install_state = status.get("installState", "unknown")
            
            if install_state == "installed":
                summary["installed"] += 1
            elif install_state == "failed":
                summary["failed"] += 1
            elif install_state in ["notInstalled", "available"]:
                summary["pending"] += 1
            else:
                summary["not_applicable"] += 1
            
            summary["devices"].append({
                "device_name": status.get("deviceName"),
                "user_name": status.get("userName"),
                "install_state": install_state,
                "error_code": status.get("errorCode"),
                "last_sync": status.get("lastSyncDateTime")
            })
        
        logger.info(f"Status: {summary['installed']} installed, {summary['failed']} failed")
        return summary
    
    # ===== Helper Methods =====
    
    def _get_default_return_codes(self) -> List[Dict]:
        """Get default return codes for Win32 apps."""
        return [
            {"returnCode": 0, "type": "success"},
            {"returnCode": 1707, "type": "success"},  # Already installed
            {"returnCode": 3010, "type": "softReboot"},
            {"returnCode": 1641, "type": "hardReboot"},
            {"returnCode": 1618, "type": "retry"}
        ]
