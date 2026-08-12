"""Uvicorn / Lambda entry: `uvicorn main:app --host 127.0.0.1 --port 8000`."""

from northmill.api.app import app, handler

__all__ = ["app", "handler"]
