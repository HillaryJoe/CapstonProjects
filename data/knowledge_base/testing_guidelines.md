# Test Case Writing Guidelines

## General Principles

1. **Clear Test Objectives**
   - Each test case must have a clear purpose
   - Test one thing at a time
   - Avoid overlapping test scenarios

2. **Test Case Structure**
   Every test case must include:
   - Unique ID (e.g., TC-001)
   - Descriptive title
   - Prerequisites
   - Step-by-step instructions
   - Expected results
   - Priority (High/Medium/Low)

3. **Naming Convention**
   - Format: TC-[MODULE]-[NUMBER]
   - Example: TC-AUTH-001, TC-PAY-045
   - Use descriptive names that explain what is being tested

## Security Testing

1. **Authentication Tests**
   - Test 2FA for admin users (mandatory)
   - Test session timeout (30 minutes default)
   - Test JWT token expiration
   - Test rate limiting (5 failed attempts = 15 min lockout)

2. **Input Validation**
   - Test SQL injection prevention
   - Test XSS prevention
   - Test CSRF token validation

3. **Authorization Tests**
   - Test role-based access control
   - Test horizontal privilege escalation
   - Test vertical privilege escalation

## API Testing Standards

1. **HTTP Methods**
   - GET: Read operations (no body)
   - POST: Create operations
   - PUT: Full update
   - PATCH: Partial update
   - DELETE: Remove operations

2. **Response Codes**
   - 200: Success
   - 201: Created
   - 400: Bad request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not found
   - 500: Server error

3. **Rate Limiting**
   - Standard: 100 requests per minute per user
   - Admin: 1000 requests per minute
   - Public: 10 requests per minute

## Edge Cases to Cover

1. **Boundary Testing**
   - Minimum values
   - Maximum values
   - Just below minimum
   - Just above maximum

2. **Empty/Null Values**
   - Empty strings
   - Null values
   - Whitespace only

3. **Special Characters**
   - Unicode characters
   - SQL injection patterns
   - XSS payloads

## Test Priority Guidelines

**High Priority:**
- Security vulnerabilities
- Data loss scenarios
- Payment processing
- Core functionality

**Medium Priority:**
- Non-critical features
- UI/UX issues
- Performance optimizations

**Low Priority:**
- Cosmetic issues
- Nice-to-have features
- Edge cases with low probability
