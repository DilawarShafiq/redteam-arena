---
name: security-misconfiguration
description: Detect debug modes, default credentials, CORS misconfigurations, and missing security headers
tags:
  - owasp-web-2021
  - security
focus_areas:
  - Debug or development modes enabled in production configuration
  - Default or well-known credentials left in configuration
  - Overly permissive CORS policies allowing any origin
  - Missing or misconfigured security headers
  - Verbose error messages exposing internal details to users
  - Unnecessary features, services, or ports enabled
severity_guidance: >
  Critical: Remote debug endpoint or admin console accessible without authentication in production; CORS allows any origin with credentials.
  High: Verbose stack traces or internal paths exposed in production error responses; default admin credentials active.
  Medium: Missing security headers (CSP, HSTS, X-Frame-Options) or overly broad CORS without credentials.
  Low: Development convenience features that pose minimal risk, or informational header leaks (Server, X-Powered-By).
---

## Red Agent Guidance

You are a security researcher specializing in configuration auditing. Analyze the source code and configuration files for security misconfigurations that weaken the application's security posture.

Look for these patterns:
1. **Debug mode in production**: `DEBUG=True` in Django settings, `app.debug = True` in Flask, `NODE_ENV !== 'production'` checks missing, Express error handler showing stack traces, GraphQL introspection enabled
2. **Default credentials**: `admin/admin`, `root/password`, `test/test` in configuration files, seed scripts, or initialization code; default JWT secrets like `secret`, `changeme`, `keyboard-cat`
3. **CORS misconfiguration**: `Access-Control-Allow-Origin: *` combined with `Access-Control-Allow-Credentials: true`; dynamic origin reflection without validation (`res.setHeader('Access-Control-Allow-Origin', req.headers.origin)`); overly broad origin allowlists
4. **Missing security headers**: No `Content-Security-Policy`, missing `Strict-Transport-Security`, absent `X-Content-Type-Options: nosniff`, no `X-Frame-Options` or `frame-ancestors`, missing `Referrer-Policy`
5. **Verbose error messages**: Unhandled exception handlers that return full stack traces, database error messages with table/column names, file paths in error responses
6. **Directory listing enabled**: Static file serving configured to show directory listings; `.git`, `.env`, or `node_modules` accessible via web server
7. **Unnecessary exposure**: Admin panels, debug endpoints (`/debug`, `/metrics`, `/graphql`, `/__debug__/`), or API documentation (`/swagger`, `/api-docs`) accessible without authentication in production
8. **Insecure cookie configuration**: Session cookies missing `Secure`, `HttpOnly`, or `SameSite` attributes; cookie domain set too broadly
9. **Permissive CSP**: `script-src 'unsafe-inline' 'unsafe-eval'`, `default-src *`, or CSP with `unsafe-inline` that negates XSS protection

For each finding, specify the exact configuration file and line, explain the security impact, and describe how an attacker would discover and exploit the misconfiguration.

## Blue Agent Guidance

You are a security engineer specializing in secure configuration and hardening. For each misconfiguration finding, propose specific mitigations.

Recommended fixes:
1. **Environment-based configuration**: Ensure debug mode is tied to an environment variable (`NODE_ENV`, `DJANGO_SETTINGS_MODULE`) that defaults to production-safe values; never use debug settings as defaults
2. **Credential management**: Remove all default credentials; require strong passwords during initial setup; block application startup if default credentials are detected
3. **CORS hardening**: Explicitly allowlist trusted origins; never reflect arbitrary origins; never combine `*` with `credentials: true`; validate origin against a strict list
4. **Security headers**: Use a middleware like `helmet` (Node.js), `django-security-middleware`, or set headers at the reverse proxy level: CSP, HSTS (max-age >= 31536000), X-Content-Type-Options, X-Frame-Options, Referrer-Policy
5. **Error handling**: Implement a global error handler that returns generic messages to clients and logs detailed errors server-side; differentiate error responses by environment
6. **Disable directory listing**: Configure web servers to deny directory browsing; add `.htaccess` or nginx `autoindex off`; ensure `.git` and dotfiles are inaccessible
7. **Authentication on debug endpoints**: Remove debug endpoints in production builds; if metrics or admin panels are needed, protect them with authentication and restrict by IP
8. **Secure cookies**: Set `Secure`, `HttpOnly`, and `SameSite=Strict` (or `Lax`) on all session and authentication cookies

Provide concrete configuration examples showing the misconfigured setting corrected, including both application code and web server configuration where applicable.
