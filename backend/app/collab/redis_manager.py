"""
Redis Manager for Collaborative Editing
Handles pub/sub for real-time broadcasting of operations
"""
import redis
import json
import asyncio
import os
from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    """Manages Redis connections and pub/sub for collaborative editing"""
    
    def __init__(self, redis_url: str = None):
        # Use environment variable or default to Docker Redis service
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscribers: Dict[str, List[Callable]] = {}
        
    async def publish_operation(self, document_id: str, operation: Dict[str, Any]) -> None:
        """Publish an operation to Redis channel"""
        try:
            channel = f"doc:{document_id}:operations"
            message = json.dumps(operation)
            self.redis_client.publish(channel, message)
            logger.info(f"Published operation to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing operation: {e}")
    
    async def publish_presence_update(self, document_id: str, presence_data: Dict[str, Any]) -> None:
        """Publish presence update to Redis channel"""
        try:
            channel = f"doc:{document_id}:presence"
            message = json.dumps(presence_data)
            self.redis_client.publish(channel, message)
            logger.info(f"Published presence update to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing presence update: {e}")
    
    async def publish_comment(self, document_id: str, comment_data: Dict[str, Any]) -> None:
        """Publish comment to Redis channel"""
        try:
            channel = f"doc:{document_id}:comments"
            message = json.dumps(comment_data)
            self.redis_client.publish(channel, message)
            logger.info(f"Published comment to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing comment: {e}")
    
    async def publish_cursor_update(self, document_id: str, cursor_data: Dict[str, Any]) -> None:
        """Publish cursor position update to Redis channel"""
        try:
            channel = f"doc:{document_id}:cursors"
            message = json.dumps(cursor_data)
            self.redis_client.publish(channel, message)
            logger.info(f"Published cursor update to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing cursor update: {e}")
    
    async def remove_document_presence(self, document_id: str) -> None:
        """Remove all presence data for a document"""
        try:
            # Remove all presence keys for this document
            pattern = f"presence:{document_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Removed {len(keys)} presence keys for document {document_id}")
        except Exception as e:
            logger.error(f"Error removing document presence: {e}")
    
    async def subscribe_to_document(self, document_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to document updates"""
        try:
            channel = f"doc:{document_id}:operations"
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            
            # Subscribe to the channel
            self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel {channel}")
        except Exception as e:
            logger.error(f"Error subscribing to document: {e}")
    
    async def subscribe_to_presence(self, document_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to presence updates"""
        try:
            channel = f"doc:{document_id}:presence"
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            
            self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to presence channel {channel}")
        except Exception as e:
            logger.error(f"Error subscribing to presence: {e}")
    
    async def subscribe_to_cursors(self, document_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to cursor updates"""
        try:
            channel = f"doc:{document_id}:cursors"
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            
            self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to cursors channel {channel}")
        except Exception as e:
            logger.error(f"Error subscribing to cursors: {e}")
    
    async def unsubscribe_from_document(self, document_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from document updates"""
        try:
            channel = f"doc:{document_id}:operations"
            if channel in self.subscribers and callback in self.subscribers[channel]:
                self.subscribers[channel].remove(callback)
                
                if not self.subscribers[channel]:
                    self.pubsub.unsubscribe(channel)
                    del self.subscribers[channel]
                    
            logger.info(f"Unsubscribed from channel {channel}")
        except Exception as e:
            logger.error(f"Error unsubscribing from document: {e}")
    
    async def start_listening(self) -> None:
        """Start listening for Redis messages"""
        try:
            while True:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_message(message)
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Error in Redis listening loop: {e}")
    
    async def _handle_message(self, message) -> None:
        """Handle incoming Redis message"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            # Call all subscribers for this channel
            if channel in self.subscribers:
                for callback in self.subscribers[channel]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def set_user_presence(self, document_id: str, user_id: str, username: str, 
                              cursor_position: int = 0, selection_start: int = 0, 
                              selection_end: int = 0) -> None:
        """Set user presence in Redis"""
        try:
            presence_key = f"presence:doc:{document_id}:user:{user_id}"
            presence_data = {
                "user_id": user_id,
                "username": username,
                "cursor_position": cursor_position,
                "selection_start": selection_start,
                "selection_end": selection_end,
                "last_seen": str(asyncio.get_event_loop().time())
            }
            
            # Set with expiration (5 minutes)
            self.redis_client.setex(presence_key, 300, json.dumps(presence_data))
            
            # Publish presence update
            await self.publish_presence_update(document_id, presence_data)
            
        except Exception as e:
            logger.error(f"Error setting user presence: {e}")
    
    async def get_active_users(self, document_id: str) -> List[Dict[str, Any]]:
        """Get active users for a document"""
        try:
            pattern = f"presence:doc:{document_id}:user:*"
            keys = self.redis_client.keys(pattern)
            
            active_users = []
            for key in keys:
                user_data = self.redis_client.get(key)
                if user_data:
                    active_users.append(json.loads(user_data))
            
            return active_users
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    async def remove_user_presence(self, document_id: str, user_id: str) -> None:
        """Remove user presence"""
        try:
            presence_key = f"presence:doc:{document_id}:user:{user_id}"
            self.redis_client.delete(presence_key)
            
            # Publish removal
            removal_data = {
                "user_id": user_id,
                "action": "remove"
            }
            await self.publish_presence_update(document_id, removal_data)
            
        except Exception as e:
            logger.error(f"Error removing user presence: {e}")
    
    def close(self) -> None:
        """Close Redis connections"""
        try:
            self.pubsub.close()
            self.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")

# Global Redis manager instance
redis_manager = RedisManager()
