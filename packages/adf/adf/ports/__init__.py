"""Ports: abstract interfaces the domain/application depend on.

Concrete implementations live in :mod:`adf.adapters`. The domain never imports
GitHub, Discord, Redis or an LLM SDK directly.
"""
