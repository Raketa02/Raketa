"""What Friends does when something happened elsewhere, and its audit line."""

from app.modules.friends.application.handlers.blocking import EndFriendshipsOnABlock
from app.modules.friends.application.handlers.log_friend_events import LogFriendEvent

__all__ = ["EndFriendshipsOnABlock", "LogFriendEvent"]
