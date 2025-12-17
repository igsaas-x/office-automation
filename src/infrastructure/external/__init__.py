"""
External integrations module

This module contains clients for external services like OpnForm.
"""

from .opnform_client import opnform_client, OpnFormClient

__all__ = ['opnform_client', 'OpnFormClient']