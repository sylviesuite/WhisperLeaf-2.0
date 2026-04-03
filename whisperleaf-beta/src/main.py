"""
Uvicorn entry for beta launcher: ``python -m uvicorn src.main:app``.

Re-exports the FastAPI application from ``src.core.main`` so the batch file can use a
stable ``src.main:app`` target without embedding ``src.core`` in the launcher.
"""

from src.core.main import app

__all__ = ["app"]
