- JWTs are NOT encrypted - Anyone can decode and read the payload

- Signing prevents tampering - Any change breaks the signature

- The signature depends on ALL parts - Can't modify header or payload

- Always use UTC for timestamps - Timezone consistency is critical

- Secrets must be strong - Minimum 32 characters for HS256

- Verify ALL claims - Especially exp (expiration)

- Use constant-time comparison - Prevent timing attacks