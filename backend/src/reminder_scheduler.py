"""
Reminder Scheduler Service
Manages scheduled reminders for WhatsApp and Email notifications.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ReminderType(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    BOTH = "both"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Reminder:
    """Reminder data structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = ""
    recipient: str = ""  # Phone number or email
    reminder_type: ReminderType = ReminderType.WHATSAPP
    scheduled_time: datetime = field(default_factory=datetime.now)
    status: ReminderStatus = ReminderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class ReminderScheduler:
    """Manages scheduling and execution of reminders."""
    
    def __init__(self):
        self.reminders: Dict[str, Reminder] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        logger.info("✅ Reminder Scheduler initialized")
    
    def schedule_reminder(
        self,
        message: str,
        recipient: str,
        reminder_type: ReminderType,
        scheduled_time: datetime,
        metadata: Optional[Dict] = None
    ) -> Reminder:
        """
        Schedule a new reminder.
        
        Args:
            message: The message to send
            recipient: Phone number (with country code) or email address
            reminder_type: Type of reminder (whatsapp, email, both)
            scheduled_time: When to send the reminder
            metadata: Optional additional data
            
        Returns:
            Reminder: The created reminder object
        """
        # Ensure scheduled_time is timezone-aware
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
        
        reminder = Reminder(
            id=str(uuid.uuid4()),
            message=message,
            recipient=recipient,
            reminder_type=reminder_type,
            scheduled_time=scheduled_time,
            status=ReminderStatus.PENDING,
            created_at=datetime.now(timezone.utc)  # Timezone-aware
        )
        
        self.reminders[reminder.id] = reminder
        logger.info(f"📅 Scheduled {reminder_type} reminder {reminder.id} for {scheduled_time}")
        
        return reminder
    
    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Get a reminder by ID."""
        return self.reminders.get(reminder_id)
    
    def list_reminders(
        self,
        status: Optional[ReminderStatus] = None,
        reminder_type: Optional[ReminderType] = None
    ) -> List[Reminder]:
        """
        List reminders with optional filtering.
        
        Args:
            status: Filter by status
            reminder_type: Filter by type
            
        Returns:
            List of reminders matching the criteria
        """
        reminders = list(self.reminders.values())
        
        if status:
            reminders = [r for r in reminders if r.status == status]
        
        if reminder_type:
            reminders = [r for r in reminders if r.reminder_type == reminder_type]
        
        return reminders
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """
        Cancel a pending reminder.
        
        Args:
            reminder_id: ID of the reminder to cancel
            
        Returns:
            bool: True if cancelled, False if not found or already sent
        """
        reminder = self.reminders.get(reminder_id)
        
        if not reminder:
            return False
        
        if reminder.status != ReminderStatus.PENDING:
            return False
        
        reminder.status = ReminderStatus.CANCELLED
        logger.info(f"🚫 Cancelled reminder {reminder_id}")
        return True
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """
        Delete a reminder.
        
        Args:
            reminder_id: ID of the reminder to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            logger.info(f"🗑️ Deleted reminder {reminder_id}")
            return True
        return False
    
    async def start(self):
        """Start the reminder scheduler background task."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("▶️ Reminder Scheduler started")
    
    async def stop(self):
        """Stop the reminder scheduler."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Reminder Scheduler stopped")
    
    async def _run_scheduler(self):
        """Background task that checks and sends due reminders."""
        logger.info("🔄 Scheduler loop started")
        
        while self.is_running:
            try:
                await self._check_and_send_reminders()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(10)
    
    async def _check_and_send_reminders(self):
        """Check for due reminders and send them."""
        try:
            # Use timezone-aware datetime for comparison
            now = datetime.now(timezone.utc)
            
            pending_reminders = [
                r for r in self.reminders.values()
                if r.status == ReminderStatus.PENDING
            ]
            
            for reminder in pending_reminders:
                # Ensure reminder.scheduled_time is timezone-aware
                scheduled_time = reminder.scheduled_time
                if scheduled_time.tzinfo is None:
                    # Make it timezone-aware if it's naive
                    scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
                
                if scheduled_time <= now:
                    # Send the reminder
                    await self._send_reminder(reminder)
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
    
    async def _send_reminder(self, reminder: Reminder):
        """
        Send a reminder (placeholder - will be implemented by notification modules).
        
        Args:
            reminder: The reminder to send
        """
        try:
            logger.info(f"📤 Attempting to send reminder {reminder.id}")
            
            # Import notification services here to avoid circular imports
            from src.whatsapp_service import send_whatsapp_message
            from src.email_service import send_email
            
            if reminder.reminder_type == ReminderType.WHATSAPP:
                await send_whatsapp_message(reminder.recipient, reminder.message)
            elif reminder.reminder_type == ReminderType.EMAIL:
                await send_email(
                    to_email=reminder.recipient,
                    subject="Reminder",
                    body=reminder.message
                )
            elif reminder.reminder_type == ReminderType.BOTH:
                # Send both WhatsApp and Email
                # Recipient should be formatted as "phone_number|email@example.com"
                parts = reminder.recipient.split("|")
                if len(parts) == 2:
                    await send_whatsapp_message(parts[0], reminder.message)
                    await send_email(parts[1], "Reminder", reminder.message)
                else:
                    raise ValueError("For 'both' type, recipient must be 'phone|email'")
            
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = datetime.now()
            logger.info(f"✅ Successfully sent reminder {reminder.id}")
            
        except Exception as e:
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = str(e)
            logger.error(f"❌ Failed to send reminder {reminder.id}: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about reminders."""
        total = len(self.reminders)
        pending = sum(1 for r in self.reminders.values() if r.status == ReminderStatus.PENDING)
        sent = sum(1 for r in self.reminders.values() if r.status == ReminderStatus.SENT)
        failed = sum(1 for r in self.reminders.values() if r.status == ReminderStatus.FAILED)
        cancelled = sum(1 for r in self.reminders.values() if r.status == ReminderStatus.CANCELLED)
        
        return {
            "total": total,
            "pending": pending,
            "sent": sent,
            "failed": failed,
            "cancelled": cancelled
        }


# Global scheduler instance
scheduler = ReminderScheduler()
