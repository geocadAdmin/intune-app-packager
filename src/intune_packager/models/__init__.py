"""
Data models for application configuration.
"""

from .app_profile import (
    ApplicationProfile,
    Installer,
    DetectionRule,
    UninstallStrategy,
    Shortcut,
    Assignment,
    CompanyPortalMetadata,
    IntuneSettings,
    IntuneRequirements,
    TestingConfig
)

__all__ = [
    "ApplicationProfile",
    "Installer",
    "DetectionRule",
    "UninstallStrategy",
    "Shortcut",
    "Assignment",
    "CompanyPortalMetadata",
    "IntuneSettings",
    "IntuneRequirements",
    "TestingConfig"
]
