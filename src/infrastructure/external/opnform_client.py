"""
OpnForm API Client

Handles communication with OpnForm API for fetching forms and managing integrations.
"""

import requests
import logging
from typing import List, Dict, Optional
from ..config.settings import settings

logger = logging.getLogger(__name__)


class OpnFormClient:
    """Client for interacting with OpnForm API"""

    def __init__(self):
        self.api_url = settings.OPNFORM_API_URL
        self.workspace_id = settings.OPNFORM_WORKSPACE_ID
        self.api_token = settings.OPNFORM_API_TOKEN

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get_forms(self) -> Optional[List[Dict]]:
        """
        Fetch all forms from OpnForm workspace

        Returns:
            List of forms with id, title, and other metadata
            None if request fails
        """
        if not self.workspace_id or not self.api_token:
            logger.error("OpnForm credentials not configured")
            return None

        try:
            url = f"{self.api_url}/workspaces/{self.workspace_id}/forms"
            logger.info(f"Fetching forms from OpnForm: {url}")

            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            # Extract forms from response
            forms = data.get('data', [])

            # Transform to simpler format for dropdown
            result = []
            for form in forms:
                result.append({
                    'id': form.get('id'),
                    'title': form.get('title'),
                    'slug': form.get('slug'),
                    'is_published': form.get('visibility') == 'public',
                    'created_at': form.get('created_at'),
                    'updated_at': form.get('updated_at')
                })

            logger.info(f"Successfully fetched {len(result)} forms from OpnForm")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forms from OpnForm: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching forms: {e}")
            return None

    def get_form_by_id(self, form_id: str) -> Optional[Dict]:
        """
        Get a specific form by ID

        Args:
            form_id: The OpnForm form ID

        Returns:
            Form details or None if not found
        """
        if not self.workspace_id or not self.api_token:
            logger.error("OpnForm credentials not configured")
            return None

        try:
            url = f"{self.api_url}/workspaces/{self.workspace_id}/forms/{form_id}"
            logger.info(f"Fetching form {form_id} from OpnForm")

            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            return data.get('data')

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching form {form_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching form: {e}")
            return None


# Singleton instance
opnform_client = OpnFormClient()
