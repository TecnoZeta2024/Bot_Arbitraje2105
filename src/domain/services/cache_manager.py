"""
CacheManager - Single responsibility for cache management.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...utils.logger import get_logger


class CacheManager:
    """
    Responsible ONLY for cache management operations.
    
    Applies Single Responsibility Principle - this class has only one reason to change:
    when cache storage or management strategy changes.
    """
    
    def __init__(self, cache_dir: str = "./cache", max_files: int = 5):
        self._cache_dir = Path(cache_dir)
        self._max_files = max_files
        self._logger = get_logger(self.__class__.__name__)
        
        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def save_market_data(
        self, 
        symbols: List[str], 
        tickers: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save market data to cache.
        
        Args:
            symbols: List of symbols
            tickers: Dictionary of tickers
            metadata: Optional metadata to store
            
        Returns:
            Path to the saved cache file
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_data_{timestamp}.json"
            filepath = self._cache_dir / filename
            
            # Prepare data structure
            cache_data = {
                "symbols": symbols,
                "tickers": tickers,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Saved market data to cache: {filepath}")
            
            # Cleanup old files
            self._cleanup_old_files()
            
            return str(filepath)
            
        except Exception as e:
            self._logger.error(f"Error saving market data to cache: {e}")
            raise CacheError(f"Failed to save cache: {e}")
    
    def load_latest_market_data(self) -> Tuple[Optional[List[str]], Optional[Dict[str, float]]]:
        """
        Load the most recent market data from cache.
        
        Returns:
            Tuple of (symbols, tickers) or (None, None) if no cache available
        """
        try:
            cache_files = self._get_cache_files()
            if not cache_files:
                self._logger.info("No cache files available")
                return None, None
            
            latest_file = cache_files[-1]  # Most recent
            return self._load_cache_file(latest_file["filepath"])
            
        except Exception as e:
            self._logger.error(f"Error loading latest cache: {e}")
            return None, None
    
    def load_cache_file(self, filepath: str) -> Tuple[Optional[List[str]], Optional[Dict[str, float]]]:
        """
        Load market data from a specific cache file.
        
        Args:
            filepath: Path to the cache file
            
        Returns:
            Tuple of (symbols, tickers) or (None, None) if loading fails
        """
        return self._load_cache_file(filepath)
    
    def _load_cache_file(self, filepath: str) -> Tuple[Optional[List[str]], Optional[Dict[str, float]]]:
        """Internal method to load cache file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            symbols = data.get("symbols", [])
            tickers = data.get("tickers", {})
            
            if not symbols or not tickers:
                self._logger.warning(f"Incomplete data in cache file: {filepath}")
                return None, None
            
            self._logger.info(f"Loaded cache from: {filepath}")
            return symbols, tickers
            
        except Exception as e:
            self._logger.error(f"Error loading cache file {filepath}: {e}")
            return None, None
    
    def list_cache_files(self) -> List[Dict[str, Any]]:
        """
        List available cache files with metadata.
        
        Returns:
            List of cache file information
        """
        return self._get_cache_files()
    
    def _get_cache_files(self) -> List[Dict[str, Any]]:
        """Get list of cache files with metadata."""
        cache_files = []
        
        if not self._cache_dir.exists():
            return cache_files
        
        for filepath in self._cache_dir.glob("market_data_*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extract metadata
                timestamp = data.get("timestamp", "unknown")
                created_at = data.get("created_at", "unknown")
                symbols_count = len(data.get("symbols", []))
                tickers_count = len(data.get("tickers", {}))
                
                # Format timestamp for display
                try:
                    if timestamp != "unknown":
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = "Unknown"
                except:
                    formatted_time = timestamp
                
                cache_info = {
                    "filepath": str(filepath),
                    "filename": filepath.name,
                    "timestamp": timestamp,
                    "formatted_time": formatted_time,
                    "created_at": created_at,
                    "symbols_count": symbols_count,
                    "tickers_count": tickers_count,
                    "file_size": filepath.stat().st_size if filepath.exists() else 0
                }
                
                cache_files.append(cache_info)
                
            except Exception as e:
                self._logger.warning(f"Error reading cache file {filepath}: {e}")
        
        # Sort by timestamp (most recent last)
        cache_files.sort(key=lambda x: x["timestamp"])
        
        return cache_files
    
    def _cleanup_old_files(self) -> None:
        """Remove old cache files, keeping only the most recent ones."""
        try:
            cache_files = self._get_cache_files()
            
            if len(cache_files) <= self._max_files:
                return
            
            # Remove oldest files
            files_to_remove = cache_files[:-self._max_files]
            
            for file_info in files_to_remove:
                try:
                    os.remove(file_info["filepath"])
                    self._logger.info(f"Removed old cache file: {file_info['filename']}")
                except Exception as e:
                    self._logger.warning(f"Failed to remove cache file {file_info['filename']}: {e}")
                    
        except Exception as e:
            self._logger.error(f"Error during cache cleanup: {e}")
    
    def clear_cache(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files removed
        """
        removed_count = 0
        
        try:
            cache_files = self._get_cache_files()
            
            for file_info in cache_files:
                try:
                    os.remove(file_info["filepath"])
                    removed_count += 1
                    self._logger.info(f"Removed cache file: {file_info['filename']}")
                except Exception as e:
                    self._logger.warning(f"Failed to remove {file_info['filename']}: {e}")
            
            self._logger.info(f"Cache cleared: {removed_count} files removed")
            
        except Exception as e:
            self._logger.error(f"Error clearing cache: {e}")
        
        return removed_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = self._get_cache_files()
            
            if not cache_files:
                return {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "oldest_file": None,
                    "newest_file": None,
                    "cache_dir": str(self._cache_dir)
                }
            
            total_size = sum(file_info["file_size"] for file_info in cache_files)
            
            return {
                "total_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file": cache_files[0]["formatted_time"] if cache_files else None,
                "newest_file": cache_files[-1]["formatted_time"] if cache_files else None,
                "cache_dir": str(self._cache_dir),
                "max_files": self._max_files
            }
            
        except Exception as e:
            self._logger.error(f"Error getting cache statistics: {e}")
            return {"error": str(e)}
    
    def is_cache_available(self) -> bool:
        """Check if any cache is available."""
        cache_files = self._get_cache_files()
        return len(cache_files) > 0
    
    def get_cache_age_seconds(self) -> Optional[int]:
        """
        Get the age of the most recent cache in seconds.
        
        Returns:
            Age in seconds or None if no cache available
        """
        try:
            cache_files = self._get_cache_files()
            if not cache_files:
                return None
            
            latest_file = cache_files[-1]
            created_at_str = latest_file.get("created_at")
            
            if not created_at_str or created_at_str == "unknown":
                return None
            
            created_at = datetime.fromisoformat(created_at_str)
            age_seconds = (datetime.now() - created_at).total_seconds()
            
            return int(age_seconds)
            
        except Exception as e:
            self._logger.error(f"Error calculating cache age: {e}")
            return None
    
    def is_cache_stale(self, max_age_seconds: int = 300) -> bool:
        """
        Check if cache is stale (older than specified age).
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 5 minutes)
            
        Returns:
            True if cache is stale or unavailable
        """
        age = self.get_cache_age_seconds()
        if age is None:
            return True  # No cache available is considered stale
        
        return age > max_age_seconds


class CacheError(Exception):
    """Exception raised for cache operations."""
    pass
