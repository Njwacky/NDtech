"""
Data Protection Management Command
Handles GDPR compliance, data retention, and privacy features
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import logging

from nano.models import (
    SecurityAuditLog, DataModificationLog, APICallLog, 
    SensitiveDataAccessLog, UserProfile, CompletedOrder, AirtimeSale
)
from confige.security import SecurityUtils, DataProtection, PrivacySettings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage data protection, GDPR compliance, and data retention'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=[
                'cleanup', 'anonymize', 'export-user', 
                'delete-user', 'retention-report', 'mask-logs'
            ],
            required=True,
            help='Action to perform'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for user-specific actions'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution without confirmation'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'cleanup':
            self.perform_data_cleanup(options)
        elif action == 'anonymize':
            self.anonymize_user_data(options)
        elif action == 'export-user':
            self.export_user_data(options)
        elif action == 'delete-user':
            self.delete_user_data(options)
        elif action == 'retention-report':
            self.generate_retention_report(options)
        elif action == 'mask-logs':
            self.mask_sensitive_logs(options)

    def perform_data_cleanup(self, options):
        """Perform automated data cleanup based on retention policies"""
        self.stdout.write("Starting data cleanup...")
        
        if options['dry_run']:
            self.stdout.write("DRY RUN - No data will be deleted")
        
        total_deleted = 0
        
        # Cleanup old security audit logs
        cutoff_date = timezone.now() - timedelta(
            days=DataProtection.get_data_retention_days()['security_logs']
        )
        
        if options['dry_run']:
            count = SecurityAuditLog.objects.filter(created_at__lt=cutoff_date).count()
            self.stdout.write(f"Would delete {count} old security audit logs")
        else:
            deleted_count = SecurityAuditLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            total_deleted += deleted_count
            self.stdout.write(f"Deleted {deleted_count} old security audit logs")
        
        # Cleanup old API call logs
        cutoff_date = timezone.now() - timedelta(
            days=DataProtection.get_data_retention_days()['api_logs']
        )
        
        if options['dry_run']:
            count = APICallLog.objects.filter(created_at__lt=cutoff_date).count()
            self.stdout.write(f"Would delete {count} old API call logs")
        else:
            deleted_count = APICallLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            total_deleted += deleted_count
            self.stdout.write(f"Deleted {deleted_count} old API call logs")
        
        # Cleanup old sensitive data access logs
        cutoff_date = timezone.now() - timedelta(
            days=DataProtection.get_data_retention_days()['user_activity']
        )
        
        if options['dry_run']:
            count = SensitiveDataAccessLog.objects.filter(created_at__lt=cutoff_date).count()
            self.stdout.write(f"Would delete {count} old sensitive data access logs")
        else:
            deleted_count = SensitiveDataAccessLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            total_deleted += deleted_count
            self.stdout.write(f"Deleted {deleted_count} old sensitive data access logs")
        
        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"Data cleanup completed. Total records deleted: {total_deleted}")
            )
        else:
            self.stdout.write(self.style.WARNING("Dry run completed. No data was deleted."))

    def anonymize_user_data(self, options):
        """Anonymize user data for GDPR compliance"""
        user_id = options.get('user_id')
        
        if not user_id:
            self.stdout.write(
                self.style.ERROR("User ID is required for anonymization")
            )
            return
        
        try:
            user = User.objects.get(id=user_id)
            
            if not options['force']:
                confirm = input(
                    f"This will anonymize all data for user {user.username} (ID: {user_id}). "
                    "This action cannot be undone. Continue? (yes/no): "
                )
                if confirm.lower() != 'yes':
                    self.stdout.write("Anonymization cancelled.")
                    return
            
            if options['dry_run']:
                self.stdout.write(f"DRY RUN - Would anonymize data for user {user.username}")
                return
            
            # Anonymize user object
            user.username = f"user_{user.id}_anonymized"
            user.email = f"user_{user.id}@anonymized.local"
            user.first_name = "Anonymized"
            user.last_name = "User"
            user.is_active = False
            user.save()
            
            # Anonymize user profile
            try:
                profile = user.userprofile
                profile.role = 'anonymous'
                profile.save()
            except UserProfile.DoesNotExist:
                pass
            
            # Anonymize completed orders
            CompletedOrder.objects.filter(
                processed_by=user
            ).update(
                customer_name='Anonymized Customer',
                customer_phone='0000000000'
            )
            
            # Anonymize airtime sales
            AirtimeSale.objects.filter(
                requested_by=user
            ).update(
                customer_phone='0000000000'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully anonymized data for user {user_id}")
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} not found")
            )

    def export_user_data(self, options):
        """Export user data for GDPR data subject request"""
        user_id = options.get('user_id')
        
        if not user_id:
            self.stdout.write(
                self.style.ERROR("User ID is required for export")
            )
            return
        
        try:
            user = User.objects.get(id=user_id)
            
            # Collect user data
            user_data = {
                'personal_info': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                    'is_active': user.is_active,
                },
                'profile': {},
                'orders': [],
                'airtime_sales': [],
                'security_logs': [],
                'api_calls': [],
                'data_modifications': [],
            }
            
            # Add profile data
            try:
                profile = user.userprofile
                user_data['profile'] = {
                    'role': profile.role,
                    'created_by': profile.created_by.username if profile.created_by else None,
                    'date_created': profile.date_created,
                }
            except UserProfile.DoesNotExist:
                pass
            
            # Add orders (with masked customer data for privacy)
            orders = CompletedOrder.objects.filter(processed_by=user)
            for order in orders:
                user_data['orders'].append({
                    'id': order.id,
                    'customer_name': SecurityUtils.mask_email(order.customer_name),
                    'customer_phone': SecurityUtils.mask_phone(order.customer_phone),
                    'total': str(order.total),
                    'payment_method': order.payment_method,
                    'completed_at': order.completed_at,
                })
            
            # Add airtime sales (with masked customer data)
            airtime_sales = AirtimeSale.objects.filter(requested_by=user)
            for sale in airtime_sales:
                user_data['airtime_sales'].append({
                    'id': sale.id,
                    'airtime_product': sale.airtime_product.name,
                    'quantity': sale.quantity,
                    'total_price': str(sale.total_price),
                    'customer_phone': SecurityUtils.mask_phone(sale.customer_phone),
                    'status': sale.status,
                    'created_at': sale.created_at,
                })
            
            # Add recent security logs (limited for privacy)
            recent_logs = SecurityAuditLog.objects.filter(
                user=user
            ).order_by('-created_at')[:50]
            
            for log in recent_logs:
                user_data['security_logs'].append({
                    'event_type': log.event_type,
                    'severity': log.severity,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at,
                })
            
            # Add recent API calls (limited for privacy)
            recent_api_calls = APICallLog.objects.filter(
                user=user
            ).order_by('-created_at')[:50]
            
            for call in recent_api_calls:
                user_data['api_calls'].append({
                    'method': call.method,
                    'endpoint': call.endpoint,
                    'status_code': call.status_code,
                    'duration_ms': call.duration_ms,
                    'created_at': call.created_at,
                })
            
            # Export to JSON file
            import json
            filename = f"user_data_export_{user_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(user_data, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"User data exported to {filename}")
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} not found")
            )

    def delete_user_data(self, options):
        """Delete all user data for GDPR right to be forgotten"""
        user_id = options.get('user_id')
        
        if not user_id:
            self.stdout.write(
                self.style.ERROR("User ID is required for deletion")
            )
            return
        
        try:
            user = User.objects.get(id=user_id)
            
            if not options['force']:
                confirm = input(
                    f"This will PERMANENTLY delete ALL data for user {user.username} (ID: {user_id}). "
                    "This action cannot be undone. Continue? (yes/no): "
                )
                if confirm.lower() != 'yes':
                    self.stdout.write("Deletion cancelled.")
                    return
            
            if options['dry_run']:
                self.stdout.write(f"DRY RUN - Would delete all data for user {user.username}")
                return
            
            # Delete related data
            deleted_count = 0
            
            # Delete user's orders
            deleted_count += CompletedOrder.objects.filter(processed_by=user).delete()[0]
            
            # Delete user's airtime sales
            deleted_count += AirtimeSale.objects.filter(requested_by=user).delete()[0]
            
            # Delete user's audit logs
            deleted_count += SecurityAuditLog.objects.filter(user=user).delete()[0]
            deleted_count += DataModificationLog.objects.filter(user=user).delete()[0]
            deleted_count += APICallLog.objects.filter(user=user).delete()[0]
            deleted_count += SensitiveDataAccessLog.objects.filter(user=user).delete()[0]
            
            # Delete user profile
            try:
                user.userprofile.delete()
                deleted_count += 1
            except UserProfile.DoesNotExist:
                pass
            
            # Delete user
            user.delete()
            deleted_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} records for user {user_id}"
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with ID {user_id} not found")
            )

    def generate_retention_report(self, options):
        """Generate data retention report"""
        self.stdout.write("Generating data retention report...")
        
        retention_days = DataProtection.get_data_retention_days()
        now = timezone.now()
        
        report = {
            'generated_at': now,
            'retention_policies': retention_days,
            'current_counts': {},
            'eligible_for_deletion': {},
        }
        
        # Security audit logs
        total_count = SecurityAuditLog.objects.count()
        report['current_counts']['security_logs'] = total_count
        
        cutoff_date = now - timedelta(days=retention_days['security_logs'])
        deletable_count = SecurityAuditLog.objects.filter(created_at__lt=cutoff_date).count()
        report['eligible_for_deletion']['security_logs'] = deletable_count
        
        # API call logs
        total_count = APICallLog.objects.count()
        report['current_counts']['api_logs'] = total_count
        
        cutoff_date = now - timedelta(days=retention_days['api_logs'])
        deletable_count = APICallLog.objects.filter(created_at__lt=cutoff_date).count()
        report['eligible_for_deletion']['api_logs'] = deletable_count
        
        # Sensitive data access logs
        total_count = SensitiveDataAccessLog.objects.count()
        report['current_counts']['sensitive_data_access'] = total_count
        
        cutoff_date = now - timedelta(days=retention_days['user_activity'])
        deletable_count = SensitiveDataAccessLog.objects.filter(created_at__lt=cutoff_date).count()
        report['eligible_for_deletion']['sensitive_data_access'] = deletable_count
        
        # Display report
        self.stdout.write("\n" + "="*60)
        self.stdout.write("DATA RETENTION REPORT")
        self.stdout.write("="*60)
        self.stdout.write(f"Generated at: {now}")
        self.stdout.write("")
        
        for log_type, count in report['current_counts'].items():
            deletable = report['eligible_for_deletion'].get(log_type, 0)
            retention_period = retention_days.get(log_type, 'N/A')
            
            self.stdout.write(f"{log_type}:")
            self.stdout.write(f"  Current count: {count}")
            self.stdout.write(f"  Retention period: {retention_period} days")
            self.stdout.write(f"  Eligible for deletion: {deletable}")
            self.stdout.write("")

    def mask_sensitive_logs(self, options):
        """Mask sensitive data in existing logs"""
        self.stdout.write("Masking sensitive data in logs...")
        
        if options['dry_run']:
            self.stdout.write("DRY RUN - No data will be modified")
        
        masked_count = 0
        
        # Mask sensitive data in security audit logs
        logs = SecurityAuditLog.objects.all()
        for log in logs:
            if log.request_data:
                # Check if data needs masking
                original_data = str(log.request_data)
                masked_data = SecurityUtils.sanitize_for_logging(log.request_data)
                
                if str(masked_data) != original_data:
                    if not options['dry_run']:
                        log.request_data = masked_data
                        log.save()
                        masked_count += 1
                    else:
                        masked_count += 1
        
        # Mask sensitive data in API call logs
        logs = APICallLog.objects.all()
        for log in logs:
            if log.request_body:
                original_body = log.request_body
                try:
                    import json
                    data = json.loads(original_body)
                    masked_data = SecurityUtils.sanitize_for_logging(data)
                    masked_body = json.dumps(masked_data)
                    
                    if masked_body != original_body:
                        if not options['dry_run']:
                            log.request_body = masked_body
                            log.save()
                            masked_count += 1
                        else:
                            masked_count += 1
                except:
                    pass
        
        if options['dry_run']:
            self.stdout.write(f"Would mask {masked_count} log entries")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully masked {masked_count} log entries")
            )
