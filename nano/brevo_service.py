"""
Brevo Email Service for futurePOS
Handles sending emails including receipts to customers using Brevo API
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)

class BrevoEmailService:
    """Brevo Email Service Class"""
    
    def __init__(self):
        """Initialize Brevo Email Service"""
        self.api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', None)
        self.sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'futurePOS')
        
        if not self.api_key:
            logger.error("Brevo API key not configured")
            raise ValueError("Brevo API key not configured")
        
        if not self.sender_email:
            logger.error("Brevo sender email not configured")
            raise ValueError("Brevo sender email not configured")
        
        # Configure Brevo API
        configuration = Configuration()
        configuration.api_key['api-key'] = self.api_key
        self.api_client = ApiClient(configuration)
        self.email_api = TransactionalEmailsApi(self.api_client)
    
    def send_receipt_email(self, order_data, customer_email, customer_name=None):
        """
        Send receipt email to customer
        
        Args:
            order_data (dict): Order information including items, totals, etc.
            customer_email (str): Customer's email address
            customer_name (str, optional): Customer's name
        
        Returns:
            dict: Result with success status and message
        """
        try:
            if not customer_email:
                return {
                    'success': False,
                    'error': 'Customer email is required'
                }
            
            # Prepare email content
            subject = f"Receipt from {self.sender_name} - Order #{order_data.get('order_id', 'N/A')}"
            
            # Generate HTML receipt
            html_content = self._generate_receipt_html(order_data, customer_name)
            
            # Create email
            send_smtp_email = {
                'sender': {
                    'email': self.sender_email,
                    'name': self.sender_name
                },
                'to': [
                    {
                        'email': customer_email,
                        'name': customer_name or 'Customer'
                    }
                ],
                'subject': subject,
                'htmlContent': html_content,
                'headers': {
                    'X-Mailin-custom': 'receipt-email'
                }
            }
            
            # Send email
            api_response = self.email_api.send_transac_email(send_smtp_email)
            
            logger.info(f"Receipt email sent successfully to {customer_email}. Message ID: {api_response.message_id}")
            
            return {
                'success': True,
                'message': 'Receipt email sent successfully',
                'message_id': api_response.message_id
            }
            
        except ApiException as e:
            error_msg = f"Brevo API error: {e.body if e.body else str(e)}"
            logger.error(f"Failed to send receipt email: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error sending receipt email: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def send_test_email(self, to_email, test_message="Test email from futurePOS"):
        """
        Send a test email to verify Brevo configuration
        
        Args:
            to_email (str): Recipient email address
            test_message (str): Test message content
        
        Returns:
            dict: Result with success status and message
        """
        try:
            html_content = f"""
            <html>
                <body>
                    <h2>Test Email from {self.sender_name}</h2>
                    <p>{test_message}</p>
                    <p>This is a test email to verify that the Brevo email service is working correctly.</p>
                    <p>Time sent: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr>
                    <p><small>Powered by futurePOS</small></p>
                </body>
            </html>
            """
            
            send_smtp_email = {
                'sender': {
                    'email': self.sender_email,
                    'name': self.sender_name
                },
                'to': [
                    {
                        'email': to_email,
                        'name': 'Test Recipient'
                    }
                ],
                'subject': f"Test Email from {self.sender_name}",
                'htmlContent': html_content
            }
            
            api_response = self.email_api.send_transac_email(send_smtp_email)
            
            logger.info(f"Test email sent successfully to {to_email}. Message ID: {api_response.message_id}")
            
            return {
                'success': True,
                'message': 'Test email sent successfully',
                'message_id': api_response.message_id
            }
            
        except ApiException as e:
            error_msg = f"Brevo API error: {e.body if e.body else str(e)}"
            logger.error(f"Failed to send test email: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error sending test email: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _generate_receipt_html(self, order_data, customer_name=None):
        """
        Generate HTML receipt content
        
        Args:
            order_data (dict): Order information
            customer_name (str, optional): Customer's name
        
        Returns:
            str: HTML content for the receipt
        """
        try:
            # Extract order information
            order_id = order_data.get('order_id', 'N/A')
            items = order_data.get('items', [])
            total_amount = order_data.get('total', 0)
            cash_received = order_data.get('cash_received', total_amount)
            change_given = order_data.get('change_given', 0)
            payment_method = order_data.get('payment_method', 'cash')
            customer_phone = order_data.get('customer_phone', 'N/A')
            processed_by = order_data.get('processed_by', 'Staff')
            order_date = order_data.get('order_date', timezone.now())
            
            # Format order date
            if hasattr(order_date, 'strftime'):
                formatted_date = order_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_date = str(order_date)
            
            # Calculate items subtotal
            items_total = sum(item.get('quantity', 0) * item.get('price', 0) for item in items)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Receipt from {self.sender_name}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .receipt-container {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        border-bottom: 2px solid #007bff;
                        padding-bottom: 20px;
                        margin-bottom: 20px;
                    }}
                    .header h1 {{
                        color: #007bff;
                        margin: 0;
                        font-size: 28px;
                    }}
                    .receipt-info {{
                        margin-bottom: 20px;
                    }}
                    .info-row {{
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 8px;
                        padding: 5px 0;
                    }}
                    .info-label {{
                        font-weight: bold;
                        color: #333;
                    }}
                    .info-value {{
                        color: #666;
                    }}
                    .items-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    .items-table th,
                    .items-table td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    .items-table th {{
                        background-color: #f8f9fa;
                        font-weight: bold;
                        color: #333;
                    }}
                    .items-table .text-right {{
                        text-align: right;
                    }}
                    .totals {{
                        margin-top: 20px;
                        border-top: 2px solid #007bff;
                        padding-top: 15px;
                    }}
                    .total-row {{
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 8px;
                        font-size: 16px;
                    }}
                    .total-row.final {{
                        font-weight: bold;
                        font-size: 18px;
                        color: #007bff;
                        border-top: 1px solid #ddd;
                        padding-top: 10px;
                        margin-top: 10px;
                    }}
                    .footer {{
                        margin-top: 30px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                        border-top: 1px solid #ddd;
                        padding-top: 20px;
                    }}
                    .thank-you {{
                        font-size: 18px;
                        color: #007bff;
                        margin-bottom: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="receipt-container">
                    <div class="header">
                        <h1>{self.sender_name}</h1>
                        <p>Official Receipt</p>
                    </div>
                    
                    <div class="receipt-info">
                        <div class="info-row">
                            <span class="info-label">Order ID:</span>
                            <span class="info-value">#{order_id}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Date:</span>
                            <span class="info-value">{formatted_date}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Customer:</span>
                            <span class="info-value">{customer_name or 'Guest'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Phone:</span>
                            <span class="info-value">{customer_phone}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Payment Method:</span>
                            <span class="info-value">{payment_method.title()}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Processed By:</span>
                            <span class="info-value">{processed_by}</span>
                        </div>
                    </div>
                    
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th class="text-right">Qty</th>
                                <th class="text-right">Price</th>
                                <th class="text-right">Total</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            # Add items to table
            for item in items:
                item_name = item.get('product', item.get('name', 'Unknown Item'))
                quantity = item.get('quantity', 0)
                price = item.get('price', 0)
                item_total = quantity * price
                
                html_content += f"""
                            <tr>
                                <td>{item_name}</td>
                                <td class="text-right">{quantity}</td>
                                <td class="text-right">R{price:.2f}</td>
                                <td class="text-right">R{item_total:.2f}</td>
                            </tr>
                """
            
            html_content += f"""
                        </tbody>
                    </table>
                    
                    <div class="totals">
                        <div class="total-row">
                            <span>Subtotal:</span>
                            <span>R{items_total:.2f}</span>
                        </div>
                        <div class="total-row">
                            <span>Cash Received:</span>
                            <span>R{cash_received:.2f}</span>
                        </div>
                        <div class="total-row">
                            <span>Change Given:</span>
                            <span>R{change_given:.2f}</span>
                        </div>
                        <div class="total-row final">
                            <span>Total Amount:</span>
                            <span>R{total_amount:.2f}</span>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="thank-you">Thank you for your purchase!</div>
                        <p>Please keep this receipt for your records.</p>
                        <p><small>Powered by {self.sender_name} POS System</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating receipt HTML: {str(e)}")
            # Return a basic HTML receipt as fallback
            return f"""
            <html>
                <body>
                    <h2>Receipt from {self.sender_name}</h2>
                    <p>Order ID: {order_data.get('order_id', 'N/A')}</p>
                    <p>Total: R{order_data.get('total', 0):.2f}</p>
                    <p>Thank you for your purchase!</p>
                </body>
            </html>
            """
    
    def test_connection(self):
        """
        Test connection to Brevo API
        
        Returns:
            dict: Result with success status and message
        """
        try:
            # Try to get account information to test API key
            from sib_api_v3_sdk import AccountApi
            account_api = AccountApi(self.api_client)
            account_data = account_api.get_account()
            
            return {
                'success': True,
                'message': 'Brevo API connection successful',
                'account_info': {
                    'email': account_data.email,
                    'company_name': account_data.company_name
                }
            }
            
        except ApiException as e:
            error_msg = f"Brevo API connection failed: {e.body if e.body else str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error testing Brevo connection: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

# Create a singleton instance
brevo_service = BrevoEmailService()

def send_receipt_email(order_data, customer_email, customer_name=None):
    """
    Convenience function to send receipt email
    
    Args:
        order_data (dict): Order information
        customer_email (str): Customer's email address
        customer_name (str, optional): Customer's name
    
    Returns:
        dict: Result with success status and message
    """
    return brevo_service.send_receipt_email(order_data, customer_email, customer_name)

def send_test_email(to_email, test_message="Test email from futurePOS"):
    """
    Convenience function to send test email
    
    Args:
        to_email (str): Recipient email address
        test_message (str): Test message content
    
    Returns:
        dict: Result with success status and message
    """
    return brevo_service.send_test_email(to_email, test_message)

def test_brevo_connection():
    """
    Convenience function to test Brevo connection
    
    Returns:
        dict: Result with success status and message
    """
    return brevo_service.test_connection()
