# Security Guidelines

- Never log raw cookies, credentials, or secrets.
- Always encrypt local artifacts using AES-256-GCM.
- Use Libsodium sealed boxes when storing GitHub Secrets.
- Rotate keys regularly and store them in a secure vault.
- Avoid storing secrets in source control; use `.env` files or environment variables.
- Ensure runtime access follows least-privilege principles.
