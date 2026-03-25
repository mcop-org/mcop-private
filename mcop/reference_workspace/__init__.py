"""Standalone reservation reference workspace."""

from mcop.reference_workspace.builder import build_reference_workspace_dataset
from mcop.reference_workspace.dashboard import write_reference_workspace_html

__all__ = [
    "build_reference_workspace_dataset",
    "write_reference_workspace_html",
]
