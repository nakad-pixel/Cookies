# Security Guidelines

## Overview

Cookie Guardian uses an **ephemeral security model** where sensitive cookie data exists only in memory during the extraction process and is immediately wiped after injection to GitHub Secrets.

## Core Principles

### 1. No Local Persistent Storage of Secrets

- Cookie values are **never written to disk**
- Database stores only metadata (repository names, timestamps, success/failure status)
- No encryption keys are required (nothing to encrypt locally)

### 2. Ephemeral Data Handling

```
Extract ──▶ Inject ──▶ Wipe
  │           │          │
Memory    GitHub      Memory
Only      Secrets     Clear
```

1. **Extraction**: Cookies extracted into Python memory
2. **Injection**: Immediately sent to GitHub Secrets API
3. **Wipe**: Secure memory clearing and garbage collection

### 3. Automatic Log Redaction

All logs are automatically redacted:
- Cookie values: `"value":"abc123"` → `"value":"[REDACTED]"`
- Authorization headers: `Authorization: Bearer token` → `Authorization: Bearer [REDACTED]`
- Passwords and tokens: Detected via pattern matching and redacted

### 4. 2FA Detection and Skip

The system **does not handle 2FA**:
- Detects 2FA requirement during login
- Immediately aborts with clear log message
- Moves to next repository
- No credentials are stored or retried

## What Gets Logged

### Safe Metadata (Logged)
- Repository names and URLs
- Extraction timestamps
- Cookie count
- Success/failure status
- 2FA detection result

### Sensitive Data (Redacted)
- Cookie values
- User credentials
- API tokens
- Authorization headers

## GitHub Secrets

Cookies are stored in GitHub Secrets using:
- **Libsodium sealed boxes** (GitHub API requirement)
- **Encryption**: Done by GitHub, using their key infrastructure
- **Decryption**: Only available to GitHub Actions workflows in the repository

## Artifacts

GitHub Actions artifacts contain only:
- Redacted logs
- No cookie values
- No credential information

Artifacts are retained for 7 days maximum.

## Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Rotate Tokens**: Regularly rotate GitHub tokens and API keys
3. **Monitor Logs**: Review logs for any unredacted sensitive data
4. **Limit Scope**: Use least-privilege GitHub tokens
5. **WARP Usage**: Enable WARP for IP rotation when available

## Incident Response

If you suspect a security issue:

1. **Revoke Tokens**: Immediately revoke any exposed GitHub tokens
2. **Rotate Secrets**: Update all stored credentials
3. **Check Audit Logs**: Review GitHub audit logs for unauthorized access
4. **Clear Artifacts**: Delete any potentially compromised workflow artifacts

## Reporting Security Issues

Please report security vulnerabilities via GitHub Security Advisories.
