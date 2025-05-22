"""
Database Infrastructure Module
Supabase integration for data persistence
"""

from .supabase_client import SupabaseClient, supabase_client

__all__ = [
    'SupabaseClient',
    'supabase_client'
]
