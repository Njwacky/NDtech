# 5 Whys register

The 5 Whys method is now applied to each security/reliability change in this workstream. Each sequence identifies the underlying process or design failure, not only the immediate symptom.

## 1. Role handling and product editing

1. Why could an unauthorized role write products? The initial permission check verified authentication but not the role.
2. Why was role checking incomplete? The role rule relied on object-level permissions, which do not reliably protect create operations.
3. Why was that design used? Authorization was split between viewset action selection and object permissions.
4. Why was it not caught? Tests did not cover every role against both create and edit operations.
5. Root cause: role policy was not a single, explicit, tested request-level business rule.

## 2. Login, stock, and order creation

1. Why could these flows regress without notice? They had no focused regression tests.
2. Why were there no focused tests? Testing was feature-by-feature and did not define the critical user journeys.
3. Why were journeys undefined? The project documented features but not acceptance criteria.
4. Why did that matter? Authentication, stock, and orders are stateful workflows where a small regression can corrupt business data.
5. Root cause: critical workflows lacked executable acceptance criteria.

## 3. Duplicate order submissions

1. Why could a retry create another order? The server treated every request as a new command.
2. Why did it do that? Orders had no client request identity or idempotency key.
3. Why was that missing? Network retries and double-clicks were not modeled as normal POS behavior.
4. Why was that risky? POS clients commonly operate over unreliable networks and users can submit twice.
5. Root cause: order creation was not designed as an idempotent operation.

## 4. Browser price tampering and totals

1. Why could a client submit a false total? The server accepted price and total values from the request body.
2. Why were those values trusted? The frontend cart was treated as the source of truth.
3. Why is that unsafe? Browser state is fully controlled by the customer.
4. Why was it possible? Server-side pricing and line-total calculation were not mandatory at order creation.
5. Root cause: business-critical pricing rules were enforced in the client instead of the server.

## 5. Airtime sales

1. Why could airtime sales fail silently or accept malformed input? The endpoint had limited focused validation coverage.
2. Why was validation incomplete? Airtime was implemented as a separate flow from ordinary POS sales.
3. Why did that create risk? Separate flows accumulated different assumptions about phone numbers, products, stock, and status.
4. Why was inconsistency not detected? Airtime lacked dedicated regression tests.
5. Root cause: airtime was not held to the same explicit input and state-transition contract as ordinary sales.

## 6. Cancellations and refunds

1. Why could an order be cancelled after completion? The endpoint did not enforce a pending-only state transition.
2. Why was that possible? Status transitions were handled procedurally rather than through a state policy.
3. Why was ownership also risky? The endpoint did not consistently distinguish the owner from managerial override roles.
4. Why was that not caught? Tests did not cover completed orders or cross-user cancellation.
5. Root cause: order lifecycle and ownership rules were not defined and tested as invariants.

## 7. Notifications

1. Why could a user potentially see the wrong notification? Visibility depended on role and target-user filtering in the viewset.
2. Why was that risky? Notifications contain operational and potentially sensitive information.
3. Why was confidence low? Visibility and read-state behavior lacked focused tests.
4. Why were tests missing? Notification behavior was treated as UI functionality instead of an access-control boundary.
5. Root cause: notification visibility was not treated as security-sensitive data authorization.

## 8. Invalid and missing input

1. Why could invalid prices or stock values reach the API? Serializer validation did not reject them.
2. Why was validation incomplete? Model fields alone did not express business constraints such as positive prices.
3. Why was that risky? Database type validity is weaker than business validity.
4. Why was it not caught? Tests focused on successful requests, not invalid boundary values.
5. Root cause: input validation lacked explicit business invariants and negative-path tests.

## 9. Cross-user data access

1. Why could a cashier potentially access another user's data? Some querysets returned all records to any authenticated user.
2. Why was that allowed? Authentication was treated as sufficient for read access.
3. Why was that incorrect? Authentication proves identity, not authorization scope.
4. Why was it not caught? Tests did not create two users and assert isolation.
5. Root cause: data ownership and role scope were not applied consistently at queryset boundaries.

## 10. CSRF protection

1. Why were CSRF exemptions present? They made browser POST requests work without handling CSRF tokens.
2. Why was that dangerous? Session-authenticated browser requests remained forgeable by another site.
3. Why were exemptions used broadly? Browser handlers and external integration endpoints were not separated.
4. Why was that not caught? CSRF exemptions were not reviewed as part of endpoint threat modeling.
5. Root cause: transport/authentication boundaries were unclear, so convenience exemptions replaced an explicit client security contract.

## 11. Checkout transaction safety

1. Why could two checkout requests oversell stock or create inconsistent records? Stock reads and writes were not protected by row locks across the complete checkout operation.
2. Why were they not protected? Checkout created the completed order, sale records, and stock updates as separate unprotected operations.
3. Why was that risky? A POS checkout is one business transaction: partial success is not a valid state.
4. Why was the risk hard to detect? Tests covered individual success paths but not database atomicity, insufficient stock, or repeated state transitions.
5. Root cause: checkout did not model inventory and order state changes as one locked, atomic state transition.

### Corrective action

- Wrap checkout in `transaction.atomic`.
- Lock the pending order with `select_for_update()`.
- Lock each product row with `select_for_update()` before checking or changing stock.
- Reject non-pending orders.
- Recalculate sale line totals from the database product price.
- Add regression tests for insufficient stock and successful atomic stock decrement.

## 12. Rate limiting

1. Why could login or checkout be abused with repeated requests? There was no request-frequency control at the view boundary.
2. Why was there no control? Authentication and business validation were treated as sufficient protection.
3. Why is that insufficient? Valid requests can still be automated for credential attacks or accidental retry storms.
4. Why was the risk easy to miss? Rate limits were not part of the acceptance criteria for sensitive endpoints.
5. Root cause: abuse resistance was not modeled as part of endpoint security.

### Corrective action

- Add cache-backed per-client limits to login and checkout.
- Return HTTP 429 without exposing sensitive details.
- Move to a shared production cache such as Redis for multi-instance deployments.
- Add endpoint-specific limits for scanning, airtime, and external integrations before exposing them publicly.

## 13. Sensitive request logging

1. Why did tests report request-body logging errors? Middleware tried to access `request.body` after a parser or view had consumed the request stream.
2. Why was raw body access used? The audit logger attempted to capture broad request context for diagnostics.
3. Why is that unsafe? Raw bodies can contain passwords, CSRF tokens, payment details, and customer data.
4. Why was this not prevented earlier? Logging policy focused on masking known keys after capture rather than avoiding capture by default.
5. Root cause: observability was designed around collecting sensitive input instead of collecting minimal safe metadata.

### Corrective action

- Stop reading raw bodies in security middleware.
- Store only method, path, status, timing, and explicitly safe metadata.
- Redact request bodies for write requests.
- Use endpoint-specific structured fields when a business audit requires details.

## 14. Request validation with serializers

1. Why could malformed order input reach view logic? The view parsed raw JSON and performed validation in several manual branches.
2. Why was that fragile? Manual validation can drift between endpoints and may omit fields or boundary cases.
3. Why was that risky? Invalid quantities and identifiers reach business logic before a consistent error contract is applied.
4. Why was it not caught? Validation rules were not represented as reusable schemas with focused negative tests.
5. Root cause: request structure and business constraints were not expressed as a single reusable input contract.

### Corrective action

- Add serializers for pending-order input and order items.
- Validate required fields, phone format, product IDs, and positive quantities before business logic.
- Return structured HTTP 400 validation errors.
- Keep server-side price calculation after validation.

## 15. Explicit API permission classes

1. Why could an authenticated user attempt to create or modify notifications? The viewset used one broad `IsAuthenticated` policy for both reads and writes.
2. Why was that policy too broad? Read access and administrative mutation were not separated by action.
3. Why is that risky? Authentication identifies a user but does not grant permission to publish or alter system notifications.
4. Why was it not caught? Tests covered visibility and read state but not mutation permissions.
5. Root cause: API actions did not have an explicit permission matrix.

### Corrective action

- Keep authenticated access for reading visible notifications.
- Require admin/manager permission for create, update, and delete actions.
- Set `created_by` from the authenticated request, never from client input.
- Add regression tests for cashier write attempts.

## 16. Audit middleware session reliability

1. Why did sensitive-data audit logging fail? It sometimes wrote a null session key into a non-null database field.
2. Why could the session key be null? A request can have a session object without an established session key.
3. Why was that assumption made? The audit code treated session presence as equivalent to a persisted session.
4. Why did this surface during tests? API and test requests often have no browser session state.
5. Root cause: audit context fields were not normalized for anonymous and sessionless requests.

### Corrective action

- Normalize missing session keys to an empty string.
- Keep audit logging best-effort so it cannot break the business request.
- Do not read raw request bodies in middleware.
- Verify sessionless API requests through regression tests.

## 17. Rate limiting scanners and airtime

1. Why could scanner and airtime endpoints be abused? They could be called repeatedly without an endpoint-specific request limit.
2. Why was login/checkout limiting not enough? Different expensive operations have different retry and abuse profiles.
3. Why is that risky? External lookups can consume provider quotas, while airtime operations can create costly duplicate actions.
4. Why was it missing? Rate limiting was initially applied only to the most obvious login and checkout paths.
5. Root cause: abuse controls were not designed per endpoint risk and cost.

### Corrective action

- Add cache-backed limits to airtime processing and UPC lookup endpoints.
- Keep limits separate by operation so one endpoint cannot exhaust another's budget.
- Use a shared Redis cache in multi-instance production.
- Add monitoring for repeated 429 responses.

## 18. Hardcoded external API credential

1. Why was an external API credential exposed in source code? The UPC integration stored the credential as a module constant.
2. Why was it stored there? Local convenience was prioritized over deployment secret management.
3. Why is that dangerous? Repository readers, logs, builds, and forks can expose a credential that may incur cost or grant provider access.
4. Why was it not caught? Secret review was focused on environment files and did not scan source constants consistently.
5. Root cause: integration credentials lacked a mandatory environment-only configuration rule.

### Corrective action

- Read the UPC credential from an environment variable.
- Add only a placeholder to `.env.example`.
- Rotate the previously exposed credential with the provider immediately.
- Add secret scanning to CI before merging future changes.

## 19. Secret scanning and tracked environment files

1. Why could credentials be exposed? A local environment file was tracked by Git, and source/documentation had not been automatically scanned.
2. Why was the environment file tracked? Ignore rules do not remove files that were already committed.
3. Why was this not caught? CI had build and test checks but no secret-detection gate.
4. Why is that risky? Future commits can reintroduce credentials even after a manual cleanup.
5. Root cause: secret management was treated as a developer convention rather than an enforced repository control.

### Corrective action

- Remove `.env` from Git tracking while keeping `.env.example` as the safe template.
- Add Gitleaks to CI.
- Rotate any credential that was ever committed.
- Review and approve false positives explicitly; never bypass a real secret finding.

## Working rule

For every future feature or fix, record:

1. The visible failure.
2. Five causal questions.
3. The root design/process cause.
4. The code change that addresses it.
5. A regression test proving the failure cannot return.
