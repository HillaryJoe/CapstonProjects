# API Documentation

## Authentication API

### POST /api/auth/login
**Description:** Authenticate user and return JWT token

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "user": {
    "id": "123",
    "email": "user@example.com",
    "role": "user"
  }
}

```

**Security Requirements:**

- Admin users: 2FA required
- Rate limit: 5 attempts per 15 minutes
- Failed attempts: Lock account after 5 failures
- Session timeout: 30 minutes

**Error Responses:**

- 401: Invalid credentials
- 429: Too many attempts
- 403: Account locked

---

### POST /api/auth/refresh

**Description:** Refresh expired JWT token

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}

```

---

## User Management API

### POST /api/users

**Description:** Create new user

**Headers:**

```
Authorization: Bearer {access_token}
Content-Type: application/json

```

**Request:**

```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "role": "user"
}

```

**Validation Rules:**

- Email: Valid format, unique
- Password: Min 8 chars, 1 uppercase, 1 number, 1 special char
- Name: Min 2 chars, max 100 chars
- Role: "user" | "admin" | "moderator"

**Response (201 Created):**

```json
{
  "id": "456",
  "email": "newuser@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2026-01-06T10:00:00Z"
}

```

---

### GET /api/users/:id

**Description:** Get user by ID

**Authorization:** Admin only or own user ID

**Response (200 OK):**

```json
{
  "id": "456",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2026-01-06T10:00:00Z",
  "last_login": "2026-01-06T12:30:00Z"
}

```

---

## Rate Limiting

**Global Limits:**

- Unauthenticated: 10 requests/minute
- Authenticated: 100 requests/minute
- Admin: 1000 requests/minute

**Headers:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641472800

```

**Response (429 Too Many Requests):**

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}

```
