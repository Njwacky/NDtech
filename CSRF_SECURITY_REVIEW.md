# CSRF security review

Reviewed all `@csrf_exempt` decorators in the application.

## Decision

The decorators were removed from browser-facing, authenticated, scanner, checkout-adjacent, airtime, notification, food-ordering, UPC, export, and tracking handlers. These endpoints use Django sessions and must receive the normal CSRF token.

API clients should use DRF authentication and send the CSRF token when session authentication is enabled. Do not re-add `@csrf_exempt` to make a frontend request work; fix the client to obtain and send the CSRF token instead.

## Remaining integration work

If an endpoint must accept requests from a non-browser service, give it a dedicated token-authenticated endpoint and explicit `IsAuthenticated` permission. Do not exempt the existing session endpoint. Add rate limiting before exposing public integrations.

## Review rules

- Browser POST/PUT/PATCH/DELETE requests: normal Django CSRF protection.
- DRF endpoints: explicit authentication and permission classes.
- Authentication, checkout, airtime, scanner, and error-reporting endpoints: rate limit them.
- Responses and logs: never include passwords, tokens, secrets, or full sensitive request bodies.
- Validate request bodies with serializers or explicit schemas before writing data.
