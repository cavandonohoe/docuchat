"""Domain-specific exceptions surfaced through the API."""

from __future__ import annotations


class DocuchatError(Exception):
    """Base error for application-level failures."""


class UnsupportedFileType(DocuchatError):
    """Raised when an uploaded file's content type is not supported."""


class FileTooLarge(DocuchatError):
    """Raised when an uploaded file exceeds the configured size limit."""


class DocumentNotFound(DocuchatError):
    """Raised when a referenced document does not exist."""


class EmbeddingError(DocuchatError):
    """Raised when the embedding provider fails irrecoverably."""


class GenerationError(DocuchatError):
    """Raised when the chat completion provider fails irrecoverably."""
