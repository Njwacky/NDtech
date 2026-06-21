# Multi-Tenancy Data Isolation Fix

The "deep logic error" causing the app to not work properly (e.g., items not showing up after being created, sales disappearing, notifications not appearing) is due to incomplete multi-tenancy implementation. While queries are correctly filtered by the user's `Workspace`, several key components of the application are creating objects *without* assigning them to the current user's `Workspace`. As a result, these objects become "orphaned" and invisible to everyone except superusers (or no one).

## User Review Required

> [!IMPORTANT]
> This plan addresses the core logic flaw in object creation. All recent activity and audit logs that were created without a workspace will remain orphaned. If you want to retroactively fix the orphaned data, let me know, but this plan focuses on preventing future occurrences.

## Open Questions

> [!WARNING]
> Do you want me to write a quick script to fix historical data (assign orphaned objects to the workspace of the user who created them), or is fixing the code moving forward sufficient?

## Proposed Changes

We will perform a comprehensive update to inject `workspace` into all `.objects.create()` and `.objects.get_or_create()` calls.

### Core Views (`nano/cashier_views.py`)

#### [MODIFY] `nano/cashier_views.py`
- Fix `process_cashier_airtime_sale` and `process_quick_airtime_sale`.
- Inject the user's `workspace` into:
  - `AirtimeProduct.objects.get_or_create`
  - `AirtimeSale.objects.create`
  - `UserActivity.objects.create`
  - `Notification.objects.create`

### Legacy & Main Views (`nano/views_legacy.py`)

#### [MODIFY] `nano/views_legacy.py`
- Inject the user's `workspace` across several missing creation endpoints:
  - `Sale.objects.create` and `CompletedOrder.objects.create` (during checkout if missed).
  - Airtime endpoints (`AirtimeProduct`, `AirtimeSale`, `AirtimeRequest`).
  - `Notification.objects.create` loops for low stock and admin alerts.

### Food Ordering Integration (`nano/food_ordering_integration.py` & `nano/food_ordering_error_tracking.py`)

#### [MODIFY] `nano/food_ordering_integration.py`
- Inject `workspace` into `Product.objects.create`, `UserActivity.objects.create`, and `ErrorLog.objects.create`.

#### [MODIFY] `nano/food_ordering_error_tracking.py`
- Inject `workspace` into `ErrorLog.objects.create` and `UserActivity.objects.create`.

### Middlewares (`nano/middleware.py` & `nano/enhanced_security_middleware.py`)

#### [MODIFY] `nano/middleware.py`
- Inject `workspace=workspace` for all logging models if `request.user.is_authenticated`:
  - `SecurityAuditLog.objects.create`
  - `APICallLog.objects.create`
  - `SensitiveDataAccessLog.objects.create`
  - `DataModificationLog.objects.create`

#### [MODIFY] `nano/enhanced_security_middleware.py`
- Inject `workspace` into `SecurityAuditLog.objects.create`.

### API & Tests (`nano/upc_views.py` & `nano/serializers.py`)

#### [MODIFY] `nano/upc_views.py`
- Inject `workspace` into `Product.objects.create`.

#### [MODIFY] `nano/serializers.py`
- Inject `workspace` into `SensitiveDataAccessLog.objects.create`.

---

## Verification Plan

### Automated Tests
- Run the python test script `find_missing_workspace.py` again to ensure no missed `objects.create` calls without a `workspace`.

### Manual Verification
- Ask the user to act as a cashier, perform an airtime sale or checkout, and verify that it appears in their dashboard and history correctly.
