"""
Uvicorn entry for launcher scripts: ``python -m uvicorn src.main:app``.

Re-exports the FastAPI application from ``src.core.main`` so launchers can use a
stable ``src.main:app`` target.
"""

from src.core.main import app

__all__ = ["app"]
