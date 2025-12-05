"""
WhatsApp Service for sending WhatsApp reminders and notifications.
Uses WhatsApp Business Cloud API (FREE - 1000 messages/month).
Official Meta API - No browser automation needed!
"""

import os
import logging
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp notifications via Meta Business Cloud API (FREE)."""
    
    def __init__(self):
        """Initialize WhatsApp service with Meta Business API configuration."""
        self.api_token = os.getenv('WHATSAPP_API_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v21.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate that necessary configuration is present."""
        if not all([self.api_token, self.phone_number_id]):
            logger.warning("⚠️ WhatsApp Business API not configured. Set WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env")
            self.is_configured = False
        else:
            logger.info(f"✅ WhatsApp Business API initialized (FREE - 1000 msgs/month)")
            self.is_configured = True
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        preview_url: bool = False
    ) -> dict:
        """
        Send a WhatsApp text message via Meta Business Cloud API (FREE).
        
        Args:
            to_phone: Recipient phone number (with country code, e.g., "919876543210")
            message: Message text (up to 4096 characters)
            preview_url: Whether to show URL previews
            
        Returns:
            dict: Result with success status and details
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'WhatsApp Business API is not configured. See setup guide.'
            }
        
        try:
            # Clean phone number (remove + and spaces)
            clean_phone = to_phone.replace('+', '').replace(' ', '').strip()
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': clean_phone,
                'type': 'text',
                'text': {
                    'preview_url': preview_url,
                    'body': message
                }
            }
            
            logger.info(f"📱 Sending WhatsApp message to {clean_phone}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            # ✅ FIX: Check for errors BEFORE marking as success
            if not response.ok:
                error_detail = response.json() if response.text else {}
                error_msg = error_detail.get('error', {}).get('message', str(error_detail))
                
                # Check for specific WhatsApp API errors
                error_code = error_detail.get('error', {}).get('code', 0)
                
                if error_code == 131047:  # Template required
                    logger.error(f"❌ WhatsApp requires approved template for {clean_phone}. Cannot send free-form messages.")
                    return {
                        'success': False,
                        'error': 'WhatsApp Business API requires approved message templates. Free-form messages not allowed.',
                        'error_code': error_code,
                        'details': error_msg
                    }
                elif error_code == 131026:  # User opted out
                    logger.error(f"❌ User {clean_phone} has opted out of receiving messages")
                    return {
                        'success': False,
                        'error': 'User has opted out of receiving WhatsApp messages',
                        'error_code': error_code
                    }
                else:
                    logger.error(f"❌ WhatsApp API error: {error_msg}")
                    return {
                        'success': False,
                        'error': f'WhatsApp API error: {error_msg}',
                        'error_code': error_code,
                        'details': error_detail
                    }
            
            result = response.json()
            
            logger.info(f"✅ WhatsApp message sent successfully to {clean_phone}")
            
            return {
                'success': True,
                'message': 'WhatsApp message sent successfully',
                'to': clean_phone,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error sending WhatsApp: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = 'en',
        parameters: Optional[List[str]] = None
    ) -> dict:
        """
        Send a WhatsApp template message (for pre-approved templates like SOS).
        
        Args:
            to_phone: Recipient phone number (e.g., "918767491689")
            template_name: Name of approved template (e.g., "sos_btn_msg_alert")
            language_code: Language code (e.g., 'en', 'en_US')
            parameters: Template parameters [origin, destination, etc.]
            
        Returns:
            dict: Result with success status
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'WhatsApp Business API is not configured.'
            }
        
        try:
            clean_phone = to_phone.replace('+', '').replace(' ', '').strip()
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            # Build template payload
            template_payload = {
                'name': template_name,
                'language': {'code': language_code}
            }
            
            # Add parameters if provided (for template variables like {{1}}, {{2}})
            if parameters:
                template_payload['components'] = [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': param} for param in parameters]
                }]
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': clean_phone,
                'type': 'template',
                'template': template_payload
            }
            
            logger.info(f"📱 Sending WhatsApp template '{template_name}' to {clean_phone}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"✅ WhatsApp template sent successfully to {clean_phone}")
            
            return {
                'success': True,
                'message': 'WhatsApp template sent successfully',
                'to': clean_phone,
                'template': template_name,
                'message_id': result.get('messages', [{}])[0].get('id')
            }
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response else str(e)
            logger.error(f"❌ WhatsApp template error: {error_detail}")
            return {
                'success': False,
                'error': f'WhatsApp API error: {error_detail}'
            }
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp template: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_sos_message(
        self,
        to_phone: str,
        origin: str,
        destination: str,
        current_location: Optional[Dict] = None
    ) -> dict:
        """
        Send SOS alert using template message.
        
        Args:
            to_phone: Emergency contact number
            origin: Starting location
            destination: Destination location
            current_location: Dict with 'latitude' and 'longitude'
            
        Returns:
            dict: Result with success status
        """
        # Use the template from your code
        return await self.send_template_message(
            to_phone=to_phone,
            template_name='sos_btn_msg_alert',
            language_code='en',
            parameters=[origin, destination]
        )
    
    async def send_reminder_message(
        self,
        to_phone: str,
        reminder_message: str,
        scheduled_time: str
    ) -> dict:
        """Send a reminder WhatsApp message with standard format."""
        formatted_message = f"""⏰ *Reminder Notification*

{reminder_message}

📅 Scheduled for: {scheduled_time}

---
_This is an automated reminder from your Traffic Prediction System._"""
        
        return await self.send_message(to_phone, formatted_message)


# Global service instance
whatsapp_service = WhatsAppService()


# Convenience functions
async def send_whatsapp(to_phone: str, message: str) -> dict:
    """Send a WhatsApp message (convenience wrapper)."""
    return await whatsapp_service.send_message(to_phone, message)


# ✅ ADD THIS - Alias for reminder_scheduler.py compatibility
async def send_whatsapp_message(to_phone: str, message: str) -> dict:
    """
    Send WhatsApp message (alias for reminder_scheduler compatibility).
    
    Args:
        to_phone: Recipient phone number (with country code)
        message: Message text
        
    Returns:
        dict: Result with success status
    """
    return await whatsapp_service.send_message(to_phone, message)
