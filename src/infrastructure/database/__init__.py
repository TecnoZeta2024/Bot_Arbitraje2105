"""
Database Infrastructure Module
Supabase integration for data persistence
"""

from .supabase_client import SupabaseClient, get_supabase_client

__all__ = [
    'SupabaseClient',
    'get_supabase_client'
]
