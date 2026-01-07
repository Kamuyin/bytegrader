# Security Testing Quick Reference Checklist

Use this checklist alongside the comprehensive [SECURITY_TESTING.md](SECURITY_TESTING.md) guide for manual penetration testing of BYTEGrader.

## Pre-Testing Setup
- [ ] Obtain authorization to perform security testing
- [ ] Set up a non-production testing environment
- [ ] Install testing tools (Burp Suite, OWASP ZAP, Postman)
- [ ] Configure browser proxy for traffic interception
- [ ] Document the testing scope and boundaries

---

## 1. Authentication & Authorization (30 min)

### JWT/Token Security
- [ ] Decode JWT token and check for sensitive data
- [ ] Modify token payload and attempt reuse
- [ ] Change token algorithm (RS256 → HS256, 'none')
- [ ] Test token after logout
- [ ] Verify token expiration times

### LTI Authentication
- [ ] Access protected endpoints without authentication
- [ ] Modify LTI parameters (user_id, roles, context_id)
- [ ] Replay old LTI launch requests (>10 min old)
- [ ] Test with invalid signatures

### User Enumeration
- [ ] Check for different error messages for valid/invalid users
- [ ] Measure response time differences
- [ ] Test username enumeration in various endpoints

**Priority Vulnerabilities:** Authentication bypass, privilege escalation

---

## 2. Session Management (15 min)

### Session Security
- [ ] Verify session ID changes after authentication
- [ ] Test session timeout by remaining idle
- [ ] Check concurrent session handling
- [ ] Test session fixation attacks

### Cookie Security
- [ ] Verify HttpOnly flag on cookies
- [ ] Verify Secure flag on cookies (HTTPS)
- [ ] Check SameSite attribute
- [ ] Attempt to read cookies via JavaScript
- [ ] Test cookie domain/path restrictions

**Priority Vulnerabilities:** Session hijacking, cookie theft

---

## 3. Input Validation & Injection (45 min)

### SQL Injection
- [ ] Test course/assignment search: `' OR '1'='1`
- [ ] Test ID parameters: `1' UNION SELECT NULL--`
- [ ] Boolean-based blind: `' AND '1'='1`
- [ ] Time-based blind: `' AND SLEEP(5)--`
- [ ] Test all input fields and URL parameters

### Cross-Site Scripting (XSS)
- [ ] Stored XSS in course name: `<script>alert('XSS')</script>`
- [ ] Reflected XSS in search: `?q=<script>alert(1)</script>`
- [ ] DOM-based XSS in client-side rendering
- [ ] Test assignment descriptions and titles
- [ ] Test markdown cells in notebooks

### Command Injection
- [ ] Filename manipulation: `test.ipynb; ls -la`
- [ ] Path traversal in uploads: `../../etc/passwd`
- [ ] Asset path injection

### Code Injection
- [ ] Test Python code in notebooks attempting system access
- [ ] Template injection: `{{7*7}}`, `${7*7}`
- [ ] JSON injection in API requests

**Priority Vulnerabilities:** SQL injection (critical), stored XSS (high)

---

## 4. File Upload Security (20 min)

### File Type Validation
- [ ] Upload non-notebook files (.php, .exe, .jsp)
- [ ] Double extension: `notebook.ipynb.php`
- [ ] Null byte: `notebook.ipynb%00.php`
- [ ] Magic byte manipulation (rename PHP to .ipynb)

### Path Traversal
- [ ] Filename: `../../../etc/passwd`
- [ ] Filename: `..\..\..\windows\system32\config\sam`
- [ ] Asset paths with traversal sequences

### File Content
- [ ] Malformed notebook JSON
- [ ] Extremely large files (>100MB)
- [ ] Notebooks with thousands of cells
- [ ] Embedded scripts in markdown cells

**Priority Vulnerabilities:** Arbitrary file upload (critical), path traversal (high)

---

## 5. API Security (30 min)

### Authentication & Authorization
- [ ] Access all endpoints without authentication token
- [ ] Test with expired/invalid tokens
- [ ] Test each endpoint: GET, POST, PUT, DELETE, PATCH
- [ ] Verify OPTIONS, HEAD methods are handled correctly

### Rate Limiting
- [ ] Send 100+ rapid requests to same endpoint
- [ ] Attempt multiple assignment submissions rapidly
- [ ] Test login endpoint for brute force protection

### API Response Security
- [ ] Check for database errors in responses
- [ ] Look for stack traces in error responses
- [ ] Check for internal paths/system info
- [ ] Verify only necessary data is returned

### Content-Type
- [ ] Send JSON with wrong Content-Type header
- [ ] Send XML to JSON endpoints
- [ ] Test with missing Content-Type

**Priority Vulnerabilities:** Broken authentication (critical), rate limiting bypass (medium)

---

## 6. Access Control (25 min)

### Horizontal Privilege Escalation
- [ ] Access another user's submissions
- [ ] Modify another user's data
- [ ] View another user's grades
- [ ] Access courses not enrolled in

### Vertical Privilege Escalation
- [ ] Student attempts to create courses
- [ ] Student attempts to create assignments
- [ ] Student attempts to modify grades
- [ ] Student attempts to view all submissions
- [ ] Manipulate role parameters in requests

### IDOR (Insecure Direct Object Reference)
- [ ] Sequential ID enumeration (courses/1, courses/2, ...)
- [ ] Access submissions by guessing IDs
- [ ] Test with both integer and UUID IDs
- [ ] Modify IDs in URL parameters

### Missing Function Level Access
- [ ] Test hidden admin endpoints: `/api/admin/*`
- [ ] Test debug endpoints: `/api/debug`
- [ ] Test internal endpoints: `/api/internal/*`

**Priority Vulnerabilities:** IDOR (high), privilege escalation (critical)

---

## 7. LTI Integration (15 min)

### Message Validation
- [ ] Modify LTI signature and replay
- [ ] Remove required LTI parameters
- [ ] Test with expired LTI tokens
- [ ] Reuse same nonce multiple times

### OAuth/JWT
- [ ] Test token expiration validation
- [ ] Test replay attack prevention
- [ ] Verify signature validation

### Platform Security
- [ ] Attempt LTI launch from unauthorized platform
- [ ] Test platform impersonation

**Priority Vulnerabilities:** LTI authentication bypass (critical)

---

## 8. Code Execution Security (20 min)

### Notebook Sandbox
- [ ] Attempt to read `/etc/passwd`
- [ ] Attempt outbound network connections
- [ ] Attempt to spawn processes: `subprocess.run()`
- [ ] Test import restrictions
- [ ] Attempt to write to filesystem

### Arbitrary Code Execution
- [ ] Server-side template injection
- [ ] Deserialization attacks (if pickle used)
- [ ] Test Python eval/exec usage

**Priority Vulnerabilities:** Remote code execution (critical), sandbox escape (critical)

---

## 9. Configuration & Deployment (20 min)

### Secure Configuration
- [ ] Check if debug mode is enabled
- [ ] Search for hardcoded secrets in config
- [ ] Test default admin credentials
- [ ] Check for exposed configuration files

### HTTPS/TLS
- [ ] Verify TLS 1.2+ is enforced
- [ ] Test HTTP to HTTPS redirect
- [ ] Check for HSTS header
- [ ] Run SSL Labs test (ssllabs.com)

### Security Headers
- [ ] X-Frame-Options: DENY/SAMEORIGIN
- [ ] X-Content-Type-Options: nosniff
- [ ] Content-Security-Policy
- [ ] X-XSS-Protection
- [ ] Referrer-Policy
- [ ] Test CSP bypass attempts

### Directory Security
- [ ] Attempt to access `/static/` directory
- [ ] Attempt to access `/uploads/` directory
- [ ] Check for directory listing
- [ ] Access `.git/` directory
- [ ] Access `.env` files
- [ ] Access backup files (.bak, .old, .swp)

**Priority Vulnerabilities:** Exposed secrets (critical), missing security headers (low-medium)

---

## 10. Business Logic (15 min)

### Assignment Submission
- [ ] Submit assignment twice
- [ ] Submit after deadline
- [ ] Submit to wrong course
- [ ] Submit with manipulated metadata

### Grade Manipulation
- [ ] Modify submitted notebook
- [ ] Request multiple regrades
- [ ] Tamper with grade data

### Course Enrollment
- [ ] Self-enroll without authorization
- [ ] Access after unenrollment
- [ ] Test enrollment bypass

**Priority Vulnerabilities:** Business logic flaws (medium-high depending on impact)

---

## 11. Information Disclosure (15 min)

### Error Messages
- [ ] Trigger various errors and check messages
- [ ] Check for stack traces
- [ ] Check for SQL query disclosure
- [ ] Check for file paths in errors

### Source Code
- [ ] Access source files directly
- [ ] Check for exposed .git directory
- [ ] Look for backup files
- [ ] Check for config file access

### Metadata
- [ ] Check API responses for excessive metadata
- [ ] Check Server and X-Powered-By headers
- [ ] Look for version information

**Priority Vulnerabilities:** Sensitive data exposure (medium-high)

---

## Testing Tools Quick Commands

### Burp Suite
```
# Set browser proxy to 127.0.0.1:8080
# Intercept requests in Proxy tab
# Use Repeater for manual testing
# Use Intruder for automated fuzzing
```

### curl Testing
```bash
# Test endpoint without auth
curl -X GET http://localhost:8000/api/courses

# Test with token
curl -X GET http://localhost:8000/api/courses \
  -H "Authorization: Bearer <token>"

# Test SQL injection
curl -X GET "http://localhost:8000/api/courses?search=' OR '1'='1"

# Test XSS
curl -X POST http://localhost:8000/api/courses \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(1)</script>"}'

# Check headers
curl -I http://localhost:8000
```

### JWT Testing
```bash
# Decode JWT
echo "<token>" | cut -d'.' -f2 | base64 -d | jq

# Or use jwt.io website
```

### testssl.sh
```bash
# Test TLS configuration
./testssl.sh https://your-domain.com
```

---

## Priority Testing Order

### Critical Tests (Must Do First - 2 hours)
1. ✅ Authentication bypass attempts
2. ✅ SQL injection on all inputs
3. ✅ File upload restrictions
4. ✅ Access control (IDOR, privilege escalation)
5. ✅ Code execution in notebooks

### High Priority (Next - 1.5 hours)
6. ✅ XSS (stored and reflected)
7. ✅ Session management
8. ✅ API authentication
9. ✅ LTI integration security
10. ✅ Command injection

### Medium Priority (If Time Permits - 1 hour)
11. ✅ Rate limiting
12. ✅ Business logic flaws
13. ✅ Information disclosure
14. ✅ Security headers

### Low Priority (Nice to Have - 0.5 hours)
15. ✅ Error message analysis
16. ✅ Directory listing
17. ✅ Metadata exposure

**Total Estimated Time:** 5 hours for thorough manual testing

---

## Vulnerability Severity Reference

| Severity | Examples | Action |
|----------|----------|--------|
| **Critical** | SQL injection with data access, RCE, Auth bypass | Fix immediately |
| **High** | Stored XSS, Privilege escalation, Sandbox escape | Fix within 1 week |
| **Medium** | Reflected XSS, CSRF, Info disclosure | Fix within 1 month |
| **Low** | Missing headers, Verbose errors | Fix when possible |

---

## Post-Testing Activities

- [ ] Document all findings with screenshots
- [ ] Rate severity of each vulnerability
- [ ] Provide proof-of-concept for each finding
- [ ] Suggest remediation steps
- [ ] Create summary report
- [ ] Present findings to development team
- [ ] Schedule retest after fixes

---

## Common Vulnerability Patterns to Watch For

### In BYTEGrader Specifically:
- **Notebook execution sandbox escapes** - Critical concern
- **LTI parameter manipulation** - High concern
- **Student accessing other students' submissions** - High concern
- **File upload bypasses** - Critical concern
- **SQL injection in course/assignment queries** - Critical concern
- **Grade tampering** - High concern

### Quick Win Tests (5 minutes):
1. Try `GET /api/courses` without auth → Should be 401
2. Try SQL injection in search: `' OR 1=1--`
3. Upload a `.php` file as assignment
4. Access `/api/submissions/{other_user_id}`
5. Check response headers for security headers

---

## Emergency Stop Criteria

**Stop testing immediately if:**
- You gain unauthorized access to production data
- You cause service disruption
- You discover active exploitation in progress
- You access other users' real data unintentionally

Report critical findings immediately to the security team.

---

## Additional Resources

- 📄 Detailed guide: [SECURITY_TESTING.md](SECURITY_TESTING.md)
- 🌐 OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- 🌐 OWASP Top 10: https://owasp.org/www-project-top-ten/
- 🌐 PortSwigger Web Security Academy: https://portswigger.net/web-security
- 🌐 HackerOne Hacktivity: https://hackerone.com/hacktivity

---

**Remember:** Always test ethically and within the defined scope. Document everything!
