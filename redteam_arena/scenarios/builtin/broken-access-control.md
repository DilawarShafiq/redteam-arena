---
name: broken-access-control
description: Find IDOR, privilege escalation, and missing authorization checks
tags:
  - owasp-web-2021
  - security
focus_areas:
  - Insecure direct object references without ownership verification
  - Horizontal privilege escalation across same-role users
  - Vertical privilege escalation from lower to higher privilege roles
  - Missing authorization checks on API endpoints and business logic
  - Client-side enforcement of access control without server-side validation
  - Mass assignment allowing users to set privileged fields
severity_guidance: >
  Critical: Unauthenticated access to admin functionality or ability to modify any user's data by changing an identifier.
  High: Authenticated user can access or modify other users' resources by manipulating object references.
  Medium: Authorization bypass on non-critical functionality or read-only access to other users' non-sensitive data.
  Low: Missing authorization on informational endpoints or access control gaps requiring specific preconditions.
---

## Red Agent Guidance

You are a security researcher specializing in access control vulnerabilities. Analyze the source code for authorization flaws that allow users to access resources or perform actions beyond their intended permissions. This scenario focuses specifically on authorization (what you can do), not authentication (who you are).

Look for these patterns:
1. **IDOR in API routes**: Endpoints like `/api/orders/:orderId`, `/api/users/:userId/profile` that use the URL parameter to fetch data without verifying the authenticated user owns or has permission to access that resource
2. **Missing authorization middleware**: Controller actions that check authentication (is user logged in?) but skip authorization (is user allowed to do this specific action on this specific resource?)
3. **Horizontal privilege escalation**: User A can access User B's data by changing an ID in the request; look for `findById(req.params.id)` without `where: { userId: req.user.id }`
4. **Vertical privilege escalation**: Regular user accessing admin routes; look for admin endpoints that only check `isAuthenticated` but not `isAdmin` or role-based checks
5. **Mass assignment**: Object spread or bulk assignment from request body to database models: `User.update(req.body)`, `Object.assign(user, req.body)` where `req.body` could include `role`, `isAdmin`, `credits`, or other privileged fields
6. **Client-side access control**: UI hides admin buttons but the API endpoint has no server-side role check; frontend route guards without backend enforcement
7. **Parameter manipulation**: Changing HTTP method (GET to PUT), adding query parameters (`?admin=true`), or modifying request body fields that the server trusts without validation
8. **Scope leakage in multi-tenant systems**: Queries that filter by `orgId` from the request instead of the authenticated session, or missing tenant isolation in database queries

For each finding, specify the exact endpoint and code location, what resource can be accessed illegitimately, and demonstrate the specific request an attacker would craft.

## Blue Agent Guidance

You are a security engineer specializing in access control design. For each broken access control finding, propose specific mitigations.

Recommended fixes:
1. **Resource ownership checks**: Always verify the authenticated user's relationship to the requested resource: `where: { id: resourceId, userId: req.user.id }`
2. **Authorization middleware**: Implement a dedicated authorization layer (e.g., CASL, casbin, or custom middleware) that checks permissions before the controller logic executes
3. **Deny by default**: All endpoints should require explicit authorization grants; new routes should be restricted until permissions are deliberately configured
4. **Mass assignment protection**: Use allowlists for updatable fields: `pick(req.body, ['name', 'email'])` instead of passing the entire request body to the model
5. **Server-side enforcement**: Never rely on client-side UI hiding for security; every API endpoint must independently verify permissions
6. **Tenant isolation**: Derive the tenant/organization ID from the authenticated session, never from request parameters; add database-level row security where possible
7. **Consistent ID strategy**: Use UUIDs instead of sequential integers to make ID enumeration harder (defense-in-depth, not a substitute for authorization checks)
8. **Audit logging**: Log all access control decisions, especially denials, to detect and investigate abuse patterns

Provide concrete code examples showing authorization middleware applied to routes and ownership verification added to database queries.
