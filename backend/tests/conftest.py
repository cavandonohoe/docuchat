"""Pytest fixtures shared across tests."""

from __future__ import annotations

import os

# Ensure deterministic, offline-friendly settings before app imports.
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("UPLOAD_DIR", "/tmp/docuchat-tests")
os.environ.setdefault("EMBEDDING_DIM", "8")
