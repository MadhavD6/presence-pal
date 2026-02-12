"""
Rate Limiter Service for preventing brute-force attacks.
Tracks failed identification attempts per user/kiosk.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """
        Args:
            max_attempts: Maximum failed attempts allowed in window
            window_seconds: Time window in seconds (default: 5 minutes)
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        
        # In-memory storage: {identifier: [(timestamp, success), ...]}
        self.attempts: Dict[str, list] = defaultdict(list)
        
    def _clean_old_attempts(self, identifier: str):
        """Remove attempts older than the window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.attempts[identifier] = [
            (ts, success) for ts, success in self.attempts[identifier]
            if ts > cutoff
        ]
    
    def record_attempt(self, identifier: str, success: bool):
        """
        Record an identification attempt.
        
        Args:
            identifier: Unique identifier (e.g., kiosk_id, IP, etc.)
            success: Whether the attempt was successful
        """
        self._clean_old_attempts(identifier)
        self.attempts[identifier].append((datetime.now(), success))
        
        # Reset on success
        if success:
            self.attempts[identifier] = []
    
    def is_blocked(self, identifier: str) -> tuple[bool, Optional[int]]:
        """
        Check if identifier is currently blocked.
        
        Returns:
            (is_blocked, seconds_until_unblock)
        """
        self._clean_old_attempts(identifier)
        
        # Count failed attempts
        failed_count = sum(1 for _, success in self.attempts[identifier] if not success)
        
        if failed_count >= self.max_attempts:
            # Calculate when first attempt will expire
            if self.attempts[identifier]:
                oldest_ts = self.attempts[identifier][0][0]
                unblock_at = oldest_ts + timedelta(seconds=self.window_seconds)
                seconds_remaining = int((unblock_at - datetime.now()).total_seconds())
                return True, max(0, seconds_remaining)
        
        return False, None
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """Get number of attempts remaining before block."""
        self._clean_old_attempts(identifier)
        failed_count = sum(1 for _, success in self.attempts[identifier] if not success)
        return max(0, self.max_attempts - failed_count)


# Singleton instance
rate_limiter = RateLimiter(max_attempts=5, window_seconds=5)
