import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY

class EmailService:
    def __init__(self):
        self.from_email = settings.EMAIL_FROM
    
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email with token link"""
        reset_link = f"https://www.cinescopes.app/reset-password?token={reset_token}"
        
        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Reset Your CineScope Password",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Reset Your Password</h2>
                    <p>You requested to reset your password for CineScope.</p>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_link}" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin: 16px 0;">Reset Password</a>
                    <p>Or copy this link into your browser:</p>
                    <p style="color: #6b7280; font-size: 14px;">{reset_link}</p>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">This link will expire in 15 minutes.</p>
                    <p style="color: #6b7280; font-size: 14px;">If you didn't request this, ignore this email.</p>
                </div>
                """
            }
            
            resend.Emails.send(params)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
    
    async def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification link to new user"""
        verification_link = f"https://www.cinescopes.app/verify-email?token={verification_token}"
        
        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Verify Your CineScope Email",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Welcome to CineScope!</h2>
                    <p>Thanks for signing up. Please verify your email to start tracking movies and TV shows.</p>
                    <a href="{verification_link}" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; margin: 16px 0;">Verify Email</a>
                    <p>Or copy this link into your browser:</p>
                    <p style="color: #6b7280; font-size: 14px;">{verification_link}</p>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">This link will expire in 24 hours.</p>
                    <p style="color: #6b7280; font-size: 14px;">If you didn't create an account, ignore this email.</p>
                </div>
                """
            }
            
            resend.Emails.send(params)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

email_service = EmailService()