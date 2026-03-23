---
name: api-security-checklist
description: "Web app API security checklist. Provides OWASP Top 10-based vulnerability checks, authentication/authorization patterns, input validation, Rate Limiting, CORS, and SQL Injection defense as a backend-dev extension skill. Use for requests like 'API security', 'OWASP', 'SQL Injection', 'XSS defense', 'CORS configuration', 'security checklist'."
---

# API Security Checklist — Web App API Security Checklist

An OWASP-based security checklist and defense guide that the backend-dev agent uses during API development.

## Target Agent

`backend-dev` — Applies this skill's security checklist directly to API implementation.

## OWASP API Security Top 10 Check

| Rank | Vulnerability | Defense |
|------|-------------|---------|
| A1 | BOLA (Broken Object Level Authorization) | Verify object ownership at every endpoint |
| A2 | Broken Authentication | bcrypt hashing, Rate Limit |
| A3 | Broken Object Property Level Authorization | Filter fields via response schemas (Pydantic) |
| A4 | Unrestricted Resource Consumption | Rate Limiting, enforce pagination |
| A5 | Broken Function Level Authorization | RBAC middleware |
| A6 | SSRF | URL whitelist, block internal IPs |
| A7 | Security Misconfiguration | Separate production config, inspect headers |
| A8 | Automated Threats | State machine validation, server-side business rules |
| A9 | Improper Asset Management | API inventory, version deprecation policy |
| A10 | Unsafe API Consumption | Validate external responses, set timeouts |

## Input Validation Checklist

| Validation Item | Method | Tool |
|----------------|--------|------|
| Type Validation | Schema validation | Pydantic |
| Length Limits | Min/max length | Pydantic Field() |
| Pattern Matching | Email, URL, phone | Regex + Pydantic |
| SQL Injection | Parameterized queries | SQLAlchemy ORM |
| XSS | HTML escaping | Server-side escape |
| SMILES Validation | RDKit parsing | RDKit MolFromSmiles |
| File Upload | Type/size validation | MIME type verification |

## HTTP Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Content-Security-Policy` | `default-src 'self'` | Prevent XSS |

## CORS Configuration (FastAPI)

| Environment | Setting |
|------------|---------|
| Development | `origins: ["http://localhost:5173"]` |
| Production | `origins: ["https://yourdomain.com"]` — specify domains |
| Forbidden | `origins: ["*"]` with credentials — security risk |

## Rate Limiting Strategy

| Target | Limit |
|--------|-------|
| Search endpoints | 10 req/min/IP |
| General API | 100 req/min/IP |
| File download (PDB) | 30 req/min/IP |

## Error Response Security

- Never expose internal details (stack traces, SQL queries) in production
- Use consistent error format via FastAPI HTTPException
- Return generic messages for auth failures
