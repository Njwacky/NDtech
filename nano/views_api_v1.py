"""
API ViewSets for NDtech POS system v1
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    UserProfile, Product, Notification, ErrorLog, SecurityAuditLog,
    FCMToken, AirtimeProduct, AirtimeSale, WarehousePrice, PriceComparison,
    DataModificationLog, AdminActionLog, APICallLog, SensitiveDataAccessLog
)
from .serializers import (
    UserSerializer, UserProfileSerializer, ProductSerializer, NotificationSerializer,
    ErrorLogSerializer, SecurityAuditLogSerializer, FCMTokenSerializer,
    AirtimeProductSerializer, AirtimeSaleSerializer, WarehousePriceSerializer,
    PriceComparisonSerializer, DataModificationLogSerializer, AdminActionLogSerializer,
    APICallLogSerializer, SensitiveDataAccessLogSerializer
)


class IsAdminOrManager(permissions.BasePermission):
    """Custom permission to only allow admins and managers"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            return request.user.userprofile.role in ['admin', 'manager']
        except UserProfile.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        try:
            user_profile = request.user.userprofile
            return user_profile.role in ['admin', 'manager']
        except UserProfile.DoesNotExist:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners or admins"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if isinstance(obj, User):
            return obj == request.user
        
        return False


def _current_workspace(user):
    """Return the user's workspace, or None if unavailable."""
    return getattr(getattr(user, 'userprofile', None), 'workspace', None)


def _workspace_filtered(queryset, user, workspace_path='workspace'):
    """Scope a queryset to the current user's workspace.

    Superusers see all rows. Regular users see rows in their own workspace
    plus legacy rows that have no workspace assigned (workspace IS NULL).
    """
    if user.is_superuser:
        return queryset
    workspace = _current_workspace(user)
    if workspace is None:
        # No workspace assigned: only show legacy/orphaned rows.
        return queryset.filter(**{f'{workspace_path}__isnull': True})
    return queryset.filter(
        Q(**{workspace_path: workspace}) | Q(**{f'{workspace_path}__isnull': True})
    )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for User model - read only for API"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['username']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        try:
            if user.userprofile.role in ['admin', 'manager']:
                # Managers/admins see users within their own workspace.
                workspace = _current_workspace(user)
                if workspace is not None:
                    return User.objects.filter(userprofile__workspace=workspace)
                return User.objects.filter(userprofile__workspace__isnull=True)
        except UserProfile.DoesNotExist:
            pass
        return User.objects.filter(pk=user.pk)

    @extend_schema(summary="Get current user info")
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model"""
    queryset = UserProfile.objects.select_related('user', 'created_by').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['date_created', 'user__username']
    ordering = ['-date_created']

    @extend_schema(summary="Get users by role")
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get users filtered by role"""
        role = request.query_params.get('role')
        if not role:
            return Response(
                {'error': 'Role parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profiles = self.queryset.filter(role=role)
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_on_sale', 'stock']
    search_fields = ['name', 'description', 'barcode']
    ordering_fields = ['name', 'price', 'stock', 'date_added']
    ordering = ['name']

    def get_queryset(self):
        return _workspace_filtered(Product.objects.all(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(workspace=_current_workspace(self.request.user))

    def get_permissions(self):
        """Custom permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrManager]
        return super().get_permissions()

    @extend_schema(summary="Get low stock products")
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock (less than 10)"""
        threshold = request.query_params.get('threshold', 10)
        products = self.get_queryset().filter(stock__lt=threshold)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get products on sale")
    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Get products currently on sale"""
        products = [p for p in self.get_queryset() if p.is_currently_on_sale()]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get expired products")
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired products"""
        products = [p for p in self.get_queryset() if p.is_expired()]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Search by barcode")
    @action(detail=False, methods=['get'])
    def barcode_lookup(self, request):
        """Search product by barcode"""
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response(
                {'error': 'Barcode parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = self.queryset.get(barcode=barcode)
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'target_role', 'is_read', 'is_dismissed']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrManager]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """Filter notifications based on user role and target"""
        user = self.request.user
        queryset = Notification.objects.select_related(
            'created_by', 'target_user', 'product'
        ).all()

        # Non-admin users only see their own notifications or role-targeted notifications
        if not user.is_superuser:
            try:
                user_profile = user.userprofile
                user_role = user_profile.role

                # Filter by user's role or specifically targeted
                queryset = queryset.filter(
                    Q(target_user=user) |
                    Q(target_role=user_role)
                )
            except (UserProfile.DoesNotExist, AttributeError):
                queryset = queryset.filter(target_user=user)

        # Tenant isolation: never leak another workspace's notifications.
        queryset = _workspace_filtered(queryset, user)
        return queryset

    @extend_schema(summary="Mark notification as read")
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @extend_schema(summary="Mark all notifications as read")
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications visible to the current user as read.

        This covers both notifications targeted directly at the user and
        notifications broadcast to the user's role.
        """
        user_notifications = self.get_queryset().filter(is_read=False)
        count = user_notifications.update(is_read=True)
        return Response({'status': f'marked {count} notifications as read'})

    @extend_schema(summary="Get unread count")
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for ErrorLog model"""
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['error_type', 'severity', 'is_resolved']
    search_fields = ['error_message', 'user_action', 'url']
    ordering_fields = ['created_at', 'severity', 'error_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter error logs based on user role"""
        user = self.request.user
        queryset = ErrorLog.objects.select_related('user', 'resolved_by').all()

        # Non-admin users only see their own errors
        if not user.is_superuser:
            queryset = queryset.filter(user=user)

        return _workspace_filtered(queryset, user)

    def get_permissions(self):
        """Custom permissions based on action"""
        if self.action in ['update', 'partial_update', 'destroy', 'resolve']:
            self.permission_classes = [IsAuthenticated, IsAdminOrManager]
        return super().get_permissions()

    @extend_schema(summary="Resolve error")
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark error as resolved (managers/admins only)"""
        error = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')

        error.mark_resolved(request.user, resolution_notes)
        return Response({'status': 'error resolved'})

    @extend_schema(summary="Get error statistics")
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get error statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_errors': queryset.count(),
            'unresolved_errors': queryset.filter(is_resolved=False).count(),
            'by_severity': queryset.values('severity').annotate(count=Count('id')),
            'by_type': queryset.values('error_type').annotate(count=Count('id')),
            'recent_errors': queryset.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
        }
        
        return Response(stats)


class SecurityAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SecurityAuditLog model - read only"""
    serializer_class = SecurityAuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'is_resolved']
    search_fields = ['description', 'username_attempted', 'ip_address']
    ordering_fields = ['created_at', 'severity', 'event_type']
    ordering = ['-created_at']

    queryset = SecurityAuditLog.objects.select_related('user', 'resolved_by').all()

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)

    @extend_schema(summary="Get security statistics")
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get security event statistics"""
        queryset = self.queryset
        
        stats = {
            'total_events': queryset.count(),
            'unresolved_events': queryset.filter(is_resolved=False).count(),
            'by_severity': queryset.values('severity').annotate(count=Count('id')),
            'by_type': queryset.values('event_type').annotate(count=Count('id')),
            'recent_events': queryset.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
            'critical_events': queryset.filter(severity='critical').count()
        }
        
        return Response(stats)


class FCMTokenViewSet(viewsets.ModelViewSet):
    """ViewSet for FCMToken model"""
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device_type', 'is_active']
    search_fields = ['device_id', 'token']
    ordering_fields = ['created_at', 'last_used']
    ordering = ['-last_used']

    def get_queryset(self):
        """Users can only manage their own tokens"""
        user = self.request.user
        if hasattr(user, 'id') and user.id:
            return FCMToken.objects.filter(user=user)
        else:
            return FCMToken.objects.none()

    def perform_create(self, serializer):
        # Always bind the token to the authenticated user; ignore any
        # user-supplied value to prevent assigning tokens to other accounts.
        serializer.save(
            user=self.request.user,
            workspace=_current_workspace(self.request.user),
        )

    @extend_schema(summary="Deactivate token")
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate FCM token"""
        token = self.get_object()
        token.is_active = False
        token.save()
        return Response({'status': 'token deactivated'})


class AirtimeProductViewSet(viewsets.ModelViewSet):
    """ViewSet for AirtimeProduct model"""
    queryset = AirtimeProduct.objects.all()
    serializer_class = AirtimeProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['network', 'airtime_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'value', 'price', 'date_added']
    ordering = ['network', 'value']

    def get_queryset(self):
        return _workspace_filtered(AirtimeProduct.objects.all(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(workspace=_current_workspace(self.request.user))

    def get_permissions(self):
        """Custom permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrManager]
        return super().get_permissions()

    @extend_schema(summary="Get low stock airtime")
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get airtime products with low stock"""
        threshold = request.query_params.get('threshold', 5)
        products = self.get_queryset().filter(stock__lt=threshold, is_active=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class AirtimeSaleViewSet(viewsets.ModelViewSet):
    """ViewSet for AirtimeSale model"""
    serializer_class = AirtimeSaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'airtime_product']
    search_fields = ['customer_phone', 'voucher_code']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        queryset = AirtimeSale.objects.select_related(
            'airtime_product', 'requested_by', 'approved_by'
        ).all()

        # Cashiers only see their own sales
        if not user.is_superuser:
            try:
                user_profile = user.userprofile
                if user_profile.role == 'cashier':
                    queryset = queryset.filter(requested_by=user)
            except (UserProfile.DoesNotExist, AttributeError):
                queryset = queryset.filter(requested_by=user)

        return _workspace_filtered(queryset, user)

    def perform_create(self, serializer):
        # The requester is always the authenticated user; new sales start pending.
        serializer.save(
            requested_by=self.request.user,
            status='pending',
            workspace=_current_workspace(self.request.user),
        )

    def get_permissions(self):
        """Approval/rejection is restricted to managers and admins."""
        if self.action in ('approve', 'reject'):
            return [IsAuthenticated(), IsAdminOrManager()]
        return super().get_permissions()

    @extend_schema(summary="Approve sale")
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve airtime sale (managers/admins only)"""
        sale = self.get_object()
        if sale.status != 'pending':
            return Response(
                {'error': 'Sale cannot be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approval_notes = request.data.get('approval_notes', '')
        sale.status = 'approved'
        sale.approved_by = request.user
        sale.approved_at = timezone.now()
        sale.approval_notes = approval_notes
        sale.save()

        return Response({'status': 'sale approved'})

    @extend_schema(summary="Reject sale")
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject airtime sale (managers/admins only)"""
        sale = self.get_object()
        if sale.status != 'pending':
            return Response(
                {'error': 'Sale cannot be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approval_notes = request.data.get('approval_notes', '')
        sale.status = 'cancelled'
        sale.approved_by = request.user
        sale.approved_at = timezone.now()
        sale.approval_notes = approval_notes
        sale.save()

        return Response({'status': 'sale rejected'})


class WarehousePriceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for WarehousePrice model - read only"""
    queryset = WarehousePrice.objects.select_related('imported_by').all()
    serializer_class = WarehousePriceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['warehouse_name', 'category']
    search_fields = ['product_name', 'barcode']
    ordering_fields = ['date_imported', 'price', 'product_name']
    ordering = ['-date_imported']

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)


class PriceComparisonViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PriceComparison model - read only"""
    queryset = PriceComparison.objects.all()
    serializer_class = PriceComparisonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['product_name', 'barcode', 'lowest_warehouse']
    ordering_fields = ['comparison_date', 'lowest_price', 'price_difference']
    ordering = ['-comparison_date']

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)

    @extend_schema(summary="Get top savings")
    @action(detail=False, methods=['get'])
    def top_savings(self, request):
        """Get products with highest savings"""
        limit = int(request.query_params.get('limit', 10))
        comparisons = self.get_queryset().order_by('-price_difference')[:limit]
        serializer = self.get_serializer(comparisons, many=True)
        return Response(serializer.data)


class DataModificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DataModificationLog model - read only"""
    serializer_class = DataModificationLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action_type', 'sensitivity', 'content_type']
    search_fields = ['object_repr', 'reason']
    ordering_fields = ['created_at', 'sensitivity', 'action_type']
    ordering = ['-created_at']

    queryset = DataModificationLog.objects.select_related('user').all()

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)


class AdminActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AdminActionLog model - read only"""
    serializer_class = AdminActionLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action_type', 'content_type']
    search_fields = ['object_repr', 'action_message']
    ordering_fields = ['created_at', 'action_type']
    ordering = ['-created_at']

    queryset = AdminActionLog.objects.select_related('user').all()

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)


class APICallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for APICallLog model - read only"""
    serializer_class = APICallLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['endpoint_type', 'method', 'status_code', 'is_suspicious']
    search_fields = ['endpoint', 'view_name', 'user_agent']
    ordering_fields = ['created_at', 'duration_ms', 'status_code']
    ordering = ['-created_at']

    queryset = APICallLog.objects.select_related('user').all()

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)

    @extend_schema(summary="Get slow requests")
    @action(detail=False, methods=['get'])
    def slow_requests(self, request):
        """Get API requests that were slow (> 2 seconds)"""
        threshold = int(request.query_params.get('threshold_ms', 2000))
        logs = self.get_queryset().filter(duration_ms__gt=threshold)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @extend_schema(summary="Get suspicious requests")
    @action(detail=False, methods=['get'])
    def suspicious(self, request):
        """Get suspicious API requests"""
        logs = self.get_queryset().filter(is_suspicious=True)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class SensitiveDataAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SensitiveDataAccessLog model - read only"""
    serializer_class = SensitiveDataAccessLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['data_type', 'access_type', 'is_bulk_access']
    search_fields = ['object_repr', 'access_reason']
    ordering_fields = ['created_at', 'data_type', 'access_type']
    ordering = ['-created_at']

    queryset = SensitiveDataAccessLog.objects.select_related('user').all()

    def get_queryset(self):
        return _workspace_filtered(super().get_queryset(), self.request.user)

    @extend_schema(summary="Get bulk accesses")
    @action(detail=False, methods=['get'])
    def bulk_accesses(self, request):
        """Get bulk sensitive data accesses"""
        logs = self.get_queryset().filter(is_bulk_access=True)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
