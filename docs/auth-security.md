# Authentication security contract

## Production secret

Production startup fails unless `JWT_SECRET_KEY` is a non-placeholder value of
at least 32 bytes. Development and test environments may use local placeholder
values, but those values must never be copied into a production deployment.

## Password reset

Password-reset tokens are stored only as keyed hashes and expire through both
an application check and the MongoDB TTL index. Consuming a token is one atomic
`findOneAndUpdate` operation: among concurrent reset requests, at most one can
claim a valid token.

The token is consumed before password hashing and updating. If the process
fails after consumption, the user requests a new reset email; the old token is
never made reusable.

Reset links target the SPA route `/#reset?token=...`. The browser submits the token and
new password to the backend and does not persist the reset token in local storage.

## Access-token revocation

Every access token carries the user's integer `auth_version`. The same version
is stored on the user document and checked for every authenticated request.
Changing a password increments the stored version, which immediately rejects
all access tokens issued before the password change.

For compatibility, existing users and tokens without an explicit version are
treated as version `0`. Their first password reset moves the account to version
`1` and revokes those legacy tokens.
