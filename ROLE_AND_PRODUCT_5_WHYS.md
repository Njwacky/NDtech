# 5 Whys: role handling and product editing

## Problem
A cashier could reach product write endpoints even though the intended role policy allows only managers and administrators to create or edit products.

### Why 1: Why could a cashier write a product?
Because the product viewset used a permission class whose initial `has_permission()` check only verified that the user was authenticated.

### Why 2: Why was authentication treated as sufficient?
The role check was implemented mainly in `has_object_permission()`, but create and update requests do not reliably receive an object-level permission check before the write occurs.

### Why 3: Why was the permission split easy to miss?
The role policy was implicit in `get_permissions()` and scattered between authentication, profile roles, and object permissions rather than represented by a single tested policy.

### Why 4: Why was this not caught earlier?
The existing tests covered some product API behavior but did not exercise every role against both create and edit operations.

### Why 5: What is the core problem?
Authorization rules were not treated as a central, testable business rule. The application had role concepts, but not a complete permission matrix enforced consistently at the request boundary.

## Corrective action taken

- `IsAdminOrManager.has_permission()` now requires an authenticated user whose profile role is `admin` or `manager`, while allowing superusers.
- Product create, update, partial update, and delete operations use that permission policy.
- Regression tests now cover admin, manager, cashier, create, edit, and unauthenticated access.
- Product edit tests verify that successful changes persist and forbidden cashier edits do not change data.

## Follow-up

Apply the same explicit permission-matrix approach to checkout, refunds, airtime, notifications, and user-management endpoints. Add tests before changing each endpoint's behavior.
