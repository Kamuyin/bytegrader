# Manual Security Testing Guide for BYTEGrader

This document provides a comprehensive manual security testing checklist for performing penetration testing and security assessments on the BYTEGrader application. These are manual tests that should be performed by security testers to identify vulnerabilities.

## Table of Contents

1. [Authentication & Authorization Testing](#1-authentication--authorization-testing)
2. [Session Management Testing](#2-session-management-testing)
3. [Input Validation & Injection Testing](#3-input-validation--injection-testing)
4. [File Upload Security Testing](#4-file-upload-security-testing)
5. [API Security Testing](#5-api-security-testing)
6. [Access Control Testing](#6-access-control-testing)
7. [LTI Integration Security Testing](#7-lti-integration-security-testing)
8. [Database Security Testing](#8-database-security-testing)
9. [Code Execution Security Testing](#9-code-execution-security-testing)
10. [Configuration & Deployment Security](#10-configuration--deployment-security)
11. [Business Logic Testing](#11-business-logic-testing)
12. [Information Disclosure Testing](#12-information-disclosure-testing)

---

## 1. Authentication & Authorization Testing

### 1.1 JWT Token Security
**Test Objective:** Verify JWT token implementation is secure

**Manual Tests:**
1. **Token Extraction:**
   - Access the application and capture the JWT token from browser storage/cookies
   - Decode the JWT at https://jwt.io
   - Check for sensitive information in the token payload
   - Verify token expiration time is reasonable (not too long)

2. **Token Manipulation:**
   - Modify the token payload (change user ID, roles, permissions)
   - Attempt to use the modified token to access the application
   - Expected: Token should be rejected

3. **Algorithm Confusion:**
   - Change the token algorithm from RS256 to HS256 or 'none'
   - Attempt to use the modified token
   - Expected: Token should be rejected

4. **Token Reuse After Logout:**
   - Login and obtain a valid token
   - Logout
   - Attempt to use the same token
   - Expected: Token should be invalidated

### 1.2 LTI Authentication Bypass
**Test Objective:** Ensure LTI authentication cannot be bypassed

**Manual Tests:**
1. **Direct Endpoint Access:**
   - Try accessing `/api/courses`, `/api/assignments` without LTI authentication
   - Expected: Should receive 401 Unauthorized

2. **Parameter Tampering:**
   - Capture LTI launch request
   - Modify user_id, roles, or context_id parameters
   - Replay the request
   - Expected: Signature validation should fail

3. **Replay Attack:**
   - Capture a valid LTI launch request
   - Wait 10+ minutes
   - Replay the exact same request
   - Expected: Should be rejected due to timestamp/nonce validation

### 1.3 User Enumeration
**Test Objective:** Prevent user enumeration attacks

**Manual Tests:**
1. **Username Enumeration:**
   - Try the `/api/auth/whoami` endpoint with different user tokens
   - Check if error messages differ between valid and invalid users
   - Expected: Generic error messages should be returned

2. **Timing Attacks:**
   - Measure response time for valid vs invalid usernames
   - Expected: Response times should be similar

---

## 2. Session Management Testing

### 2.1 Session Fixation
**Test Objective:** Verify session IDs are regenerated after authentication

**Manual Tests:**
1. **Session ID Before/After Login:**
   - Note the session ID before authentication
   - Complete authentication
   - Check if session ID changed
   - Expected: New session ID should be generated

### 2.2 Session Timeout
**Test Objective:** Ensure sessions expire appropriately

**Manual Tests:**
1. **Idle Session:**
   - Login and remain idle for extended period
   - Attempt to access protected resources
   - Expected: Session should expire after configured timeout

2. **Concurrent Sessions:**
   - Login from two different browsers/devices with same credentials
   - Check if both sessions remain active
   - Verify session isolation

### 2.3 Cookie Security
**Test Objective:** Verify cookie security attributes

**Manual Tests:**
1. **Cookie Attributes:**
   - Inspect cookies in browser developer tools
   - Verify `HttpOnly` flag is set
   - Verify `Secure` flag is set (in production/HTTPS)
   - Verify `SameSite` attribute is set appropriately
   - Check cookie domain and path restrictions

2. **Cookie Theft:**
   - Attempt to execute JavaScript to read cookies: `document.cookie`
   - Expected: HttpOnly cookies should not be accessible

---

## 3. Input Validation & Injection Testing

### 3.1 SQL Injection
**Test Objective:** Test for SQL injection vulnerabilities

**Manual Tests:**
1. **Course/Assignment Search:**
   - Input: `' OR '1'='1`
   - Input: `'; DROP TABLE courses; --`
   - Input: `1' UNION SELECT NULL, username, password FROM users --`
   - Test in search fields, filters, and query parameters
   - Expected: Inputs should be sanitized/parameterized

2. **User ID Manipulation:**
   - Modify course_id or assignment_id parameters with SQL payloads
   - Example: `/api/courses/' OR 1=1 --/assignments`
   - Expected: Should return error or no results

### 3.2 Cross-Site Scripting (XSS)
**Test Objective:** Test for XSS vulnerabilities

**Manual Tests:**
1. **Stored XSS in Course/Assignment Names:**
   - Create course with name: `<script>alert('XSS')</script>`
   - Create assignment with description: `<img src=x onerror=alert('XSS')>`
   - Check if script executes when viewing the course/assignment
   - Expected: HTML should be escaped

2. **Reflected XSS in API Responses:**
   - Submit malicious input in API requests
   - Example: `?search=<script>alert(1)</script>`
   - Check if input is reflected in response without encoding
   - Expected: Output should be encoded

3. **DOM-based XSS:**
   - Test JavaScript-based rendering with malicious payloads
   - Check JupyterLab extension UI components
   - Expected: DOM manipulation should be secure

### 3.3 Command Injection
**Test Objective:** Test for OS command injection

**Manual Tests:**
1. **Notebook Filename Manipulation:**
   - Upload notebook with filename: `test.ipynb; ls -la`
   - Upload notebook with filename: `test.ipynb && cat /etc/passwd`
   - Expected: Filename should be sanitized

2. **Asset Path Traversal:**
   - Try uploading assets with paths: `../../etc/passwd`
   - Expected: Path should be validated and sanitized

### 3.4 Code Injection in Notebooks
**Test Objective:** Test for code injection vulnerabilities

**Manual Tests:**
1. **Malicious Notebook Cells:**
   - Create notebook with cells containing:
     ```python
     import os; os.system('cat /etc/passwd')
     ```
   - Submit for grading
   - Expected: Should execute in sandboxed environment only

2. **Python Code Injection:**
   - Test if student code can escape sandbox
   - Attempt file system access, network access, process execution
   - Expected: Should be restricted by executor environment

### 3.5 LDAP/NoSQL Injection
**Test Objective:** Test for injection in non-SQL contexts

**Manual Tests:**
1. **JSON Injection:**
   - Submit malformed JSON in API requests
   - Example: `{"name": "test", "extra": {"$gt": ""}}`
   - Expected: Should validate JSON schema strictly

---

## 4. File Upload Security Testing

### 4.1 Unrestricted File Upload
**Test Objective:** Verify file upload restrictions

**Manual Tests:**
1. **File Type Validation:**
   - Attempt to upload `.php`, `.exe`, `.jsp` files as notebooks
   - Attempt to upload files with double extensions: `notebook.ipynb.php`
   - Upload files with null bytes: `notebook.ipynb%00.php`
   - Expected: Only `.ipynb` files should be accepted for notebooks

2. **Magic Byte Verification:**
   - Create a PHP file and rename it to `.ipynb`
   - Upload the file
   - Expected: Content validation should reject non-notebook files

3. **File Size Limits:**
   - Upload extremely large files (>100MB)
   - Expected: Should enforce size limits

### 4.2 Path Traversal in Uploads
**Test Objective:** Prevent directory traversal attacks

**Manual Tests:**
1. **Traversal in Filename:**
   - Upload file with name: `../../../etc/passwd`
   - Upload file with name: `..\..\..\..\windows\system32\config\sam`
   - Expected: Filename should be sanitized

2. **Asset Path Traversal:**
   - Submit asset with path containing: `../../sensitive.txt`
   - Expected: Path should be normalized and validated

### 4.3 Malicious Notebook Content
**Test Objective:** Validate notebook structure

**Manual Tests:**
1. **Malformed Notebook JSON:**
   - Upload notebook with invalid JSON structure
   - Expected: Should validate and reject

2. **Oversized Notebook:**
   - Create notebook with thousands of cells
   - Create notebook with extremely large cell outputs
   - Expected: Should enforce reasonable limits

3. **Embedded Scripts in Notebooks:**
   - Add HTML/JavaScript in markdown cells
   - Expected: Should be sanitized when rendered

---

## 5. API Security Testing

### 5.1 API Authentication
**Test Objective:** Verify all API endpoints require authentication

**Manual Tests:**
1. **Unauthenticated Access:**
   - Access each endpoint without authentication token:
     - `GET /api/courses`
     - `GET /api/assignments`
     - `POST /api/courses/{id}/assignments`
     - `POST /api/assignments/{id}/submit`
     - `GET /api/submissions`
   - Expected: All should return 401 Unauthorized

### 5.2 API Rate Limiting
**Test Objective:** Verify rate limiting is implemented

**Manual Tests:**
1. **Rapid Requests:**
   - Send 100+ requests to the same endpoint in quick succession
   - Expected: Should be rate-limited after threshold
   - Check for HTTP 429 Too Many Requests response

2. **Submission Flooding:**
   - Attempt to submit same assignment multiple times rapidly
   - Expected: Should have rate limiting or duplicate detection

### 5.3 HTTP Methods
**Test Objective:** Verify only allowed HTTP methods work

**Manual Tests:**
1. **Method Testing:**
   - Try OPTIONS, HEAD, PUT, DELETE, PATCH on various endpoints
   - Example: `DELETE /api/courses/{id}` when only GET is allowed
   - Expected: Should return 405 Method Not Allowed

### 5.4 Content-Type Validation
**Test Objective:** Ensure proper content-type validation

**Manual Tests:**
1. **Content-Type Mismatch:**
   - Send JSON data with Content-Type: text/plain
   - Send XML data to JSON endpoints
   - Expected: Should validate and reject improper content types

### 5.5 API Response Information Disclosure
**Test Objective:** Check for sensitive data in API responses

**Manual Tests:**
1. **Verbose Error Messages:**
   - Trigger errors and check responses for:
     - Database connection strings
     - Full stack traces
     - Internal file paths
     - SQL queries
   - Expected: Generic error messages in production

2. **Sensitive Data Exposure:**
   - Check API responses for:
     - Other users' personal information
     - System configuration details
     - Database schema information
   - Expected: Only necessary data should be returned

---

## 6. Access Control Testing

### 6.1 Horizontal Privilege Escalation
**Test Objective:** Verify users cannot access other users' resources

**Manual Tests:**
1. **Access Other Users' Submissions:**
   - Login as User A and note their submission ID
   - Login as User B
   - Try to access User A's submission: `GET /api/submissions/{user_a_submission_id}`
   - Expected: Should return 403 Forbidden

2. **Modify Other Users' Data:**
   - Try to update/delete another user's submission or assignment
   - Expected: Should be denied

### 6.2 Vertical Privilege Escalation
**Test Objective:** Verify regular users cannot perform admin actions

**Manual Tests:**
1. **Student Access to Admin Functions:**
   - Login as student
   - Attempt to:
     - Create courses: `POST /api/courses`
     - Create assignments: `POST /api/courses/{id}/assignments`
     - View all submissions: `GET /api/submissions` (without filtering)
     - Modify grades
   - Expected: Should return 403 Forbidden

2. **Role Manipulation:**
   - Capture request and add/modify role parameters
   - Example: Add `"role": "admin"` to API requests
   - Expected: Server-side role validation should prevent escalation

### 6.3 Insecure Direct Object Reference (IDOR)
**Test Objective:** Test for IDOR vulnerabilities

**Manual Tests:**
1. **Sequential ID Enumeration:**
   - Access `/api/courses/1`, `/api/courses/2`, `/api/courses/3`
   - Check if you can access courses you're not enrolled in
   - Expected: Should only return accessible courses

2. **GUID vs Sequential IDs:**
   - Check if IDs are predictable sequential integers or UUIDs
   - Attempt to guess valid IDs
   - Expected: Use non-sequential UUIDs for sensitive resources

### 6.4 Missing Function Level Access Control
**Test Objective:** Verify access controls on all functions

**Manual Tests:**
1. **Hidden Endpoints:**
   - Try to discover hidden admin endpoints:
     - `/api/admin/users`
     - `/api/debug`
     - `/api/internal`
   - Expected: Should require proper authentication and authorization

---

## 7. LTI Integration Security Testing

### 7.1 LTI Message Validation
**Test Objective:** Verify LTI message signature validation

**Manual Tests:**
1. **Invalid Signature:**
   - Capture LTI launch request
   - Modify the signature
   - Replay the request
   - Expected: Should reject invalid signature

2. **Missing Required Parameters:**
   - Remove required LTI parameters (user_id, context_id, etc.)
   - Attempt launch
   - Expected: Should reject incomplete requests

### 7.2 OAuth/JWT Security in LTI
**Test Objective:** Test LTI OAuth/JWT implementation

**Manual Tests:**
1. **Token Expiration:**
   - Use an expired LTI token
   - Expected: Should reject expired tokens

2. **Token Reuse:**
   - Use the same nonce multiple times
   - Expected: Should detect and reject replay

### 7.3 Platform Impersonation
**Test Objective:** Prevent LMS platform impersonation

**Manual Tests:**
1. **Forge LTI Launch:**
   - Create a fake LTI launch from unauthorized platform
   - Expected: Should validate platform registration

---

## 8. Database Security Testing

### 8.1 SQL Injection (Comprehensive)
**Test Objective:** Thorough SQL injection testing

**Manual Tests:**
1. **Boolean-based Blind SQLi:**
   - Test conditions: `' AND '1'='1` vs `' AND '1'='2`
   - Check for differences in response
   - Expected: No SQL evaluation should occur

2. **Time-based Blind SQLi:**
   - Test payloads: `' AND SLEEP(5) --`
   - Check if response is delayed
   - Expected: No delay should occur

3. **Union-based SQLi:**
   - Test payloads: `' UNION SELECT NULL, NULL, NULL --`
   - Adjust NULL count to match column count
   - Expected: Should not execute

### 8.2 Database Configuration
**Test Objective:** Check for database security misconfigurations

**Manual Tests:**
1. **Direct Database Access:**
   - Check if database port is exposed (default: 3306/MySQL, 5432/PostgreSQL)
   - Attempt direct connection to database
   - Expected: Database should not be publicly accessible

2. **Default Credentials:**
   - Check for default database credentials in configuration files
   - Expected: Strong, unique credentials should be used

---

## 9. Code Execution Security Testing

### 9.1 Notebook Execution Sandbox
**Test Objective:** Verify sandbox restrictions

**Manual Tests:**
1. **File System Access:**
   - Create notebook cells attempting to:
     ```python
     with open('/etc/passwd', 'r') as f:
         print(f.read())
     ```
   - Expected: Should be blocked or restricted to sandbox

2. **Network Access:**
   - Attempt outbound connections:
     ```python
     import socket
     s = socket.socket()
     s.connect(('malicious.com', 80))
     ```
   - Expected: Should be blocked or restricted

3. **Process Execution:**
   - Attempt to spawn processes:
     ```python
     import subprocess
     subprocess.run(['cat', '/etc/passwd'])
     ```
   - Expected: Should be blocked or restricted

### 9.2 Arbitrary Code Execution
**Test Objective:** Test for code execution vulnerabilities

**Manual Tests:**
1. **Server-Side Template Injection:**
   - Input template syntax in various fields:
     - `{{7*7}}`
     - `${7*7}`
     - `<%= 7*7 %>`
   - Check if expressions are evaluated
   - Expected: Should be treated as literal text

2. **Deserialization Attacks:**
   - If pickle or similar used, test with malicious serialized objects
   - Expected: Should validate/sanitize deserialized data

---

## 10. Configuration & Deployment Security

### 10.1 Secure Configuration
**Test Objective:** Verify secure configuration

**Manual Tests:**
1. **Debug Mode:**
   - Check if debug mode is enabled in production
   - Look for verbose error messages, stack traces
   - Expected: Debug mode should be disabled

2. **Secret Management:**
   - Check if secrets are hardcoded in configuration files
   - Search for API keys, passwords in code/config
   - Expected: Secrets should be in environment variables or secret store

3. **Default Credentials:**
   - Test for default admin credentials (admin/admin, admin/password)
   - Expected: No default credentials should work

### 10.2 HTTPS/TLS Configuration
**Test Objective:** Verify secure transport

**Manual Tests:**
1. **SSL/TLS Version:**
   - Use SSL Labs (ssllabs.com) or testssl.sh to check TLS configuration
   - Expected: TLS 1.2+ should be enforced

2. **HTTP to HTTPS Redirect:**
   - Access application via HTTP
   - Expected: Should redirect to HTTPS

3. **HSTS Header:**
   - Check response headers for `Strict-Transport-Security`
   - Expected: HSTS should be enabled

### 10.3 Security Headers
**Test Objective:** Verify security headers are present

**Manual Tests:**
1. **Header Presence:**
   - Check for these headers in responses:
     - `X-Frame-Options: DENY` or `SAMEORIGIN`
     - `X-Content-Type-Options: nosniff`
     - `Content-Security-Policy`
     - `X-XSS-Protection: 1; mode=block`
     - `Referrer-Policy`
   - Expected: All should be present

2. **CSP Bypass:**
   - If CSP is present, try to bypass it
   - Test for unsafe-inline, unsafe-eval
   - Expected: Strict CSP without unsafe directives

### 10.4 Directory Listing
**Test Objective:** Prevent directory browsing

**Manual Tests:**
1. **Directory Access:**
   - Access directories directly:
     - `/static/`
     - `/uploads/`
     - `/assets/`
   - Expected: Directory listing should be disabled

---

## 11. Business Logic Testing

### 11.1 Assignment Submission Logic
**Test Objective:** Test for business logic flaws

**Manual Tests:**
1. **Double Submission:**
   - Submit assignment twice
   - Check if both are accepted or only the latest
   - Verify proper handling

2. **Post-Deadline Submission:**
   - Modify system time or wait until after deadline
   - Attempt to submit assignment
   - Expected: Should be rejected or marked as late

3. **Submit to Wrong Course:**
   - Attempt to submit assignment to a different course
   - Expected: Should validate course context

### 11.2 Grade Manipulation
**Test Objective:** Prevent grade tampering

**Manual Tests:**
1. **Modify Submitted Notebook:**
   - Submit assignment
   - Attempt to modify the submitted notebook file
   - Expected: Submissions should be immutable

2. **Regrade Requests:**
   - Request multiple regrades
   - Check for rate limiting or approval requirements
   - Expected: Should have controls in place

### 11.3 Course Enrollment Logic
**Test Objective:** Test enrollment controls

**Manual Tests:**
1. **Self-Enrollment:**
   - Attempt to enroll in courses without authorization
   - Expected: Should require proper enrollment process

2. **Unenrollment:**
   - Enroll in course and submit assignment
   - Unenroll
   - Check if submissions are still accessible
   - Verify access control

---

## 12. Information Disclosure Testing

### 12.1 Error Messages
**Test Objective:** Prevent information leakage via errors

**Manual Tests:**
1. **Trigger Various Errors:**
   - Malformed requests
   - Invalid IDs
   - Missing parameters
   - Database errors
   - Expected: Generic error messages only

### 12.2 Source Code Disclosure
**Test Objective:** Prevent source code exposure

**Manual Tests:**
1. **Access Source Files:**
   - Try to access:
     - `.git/` directory
     - `.env` files
     - `config.py` or similar
     - Backup files (`.bak`, `.old`, `.swp`)
   - Expected: Should not be accessible

### 12.3 Metadata Exposure
**Test Objective:** Check for excessive metadata

**Manual Tests:**
1. **API Metadata:**
   - Check API responses for:
     - Internal IDs
     - Timestamps revealing patterns
     - User enumeration data
   - Expected: Minimal metadata exposure

2. **Server Headers:**
   - Check for `Server`, `X-Powered-By` headers
   - Expected: Should not reveal technology stack details

---

## Testing Tools & Resources

### Recommended Tools:
- **Burp Suite** - Comprehensive web security testing
- **OWASP ZAP** - Open-source web app scanner
- **Postman** - API testing
- **curl** - Command-line HTTP testing
- **jwt.io** - JWT token decoding
- **sqlmap** - SQL injection testing
- **testssl.sh** - TLS/SSL testing
- **Browser DevTools** - Network inspection, cookie examination

### Testing Checklist Summary:
Before releasing to production, ensure:
- [ ] All authentication mechanisms tested
- [ ] All API endpoints require proper authorization
- [ ] Input validation on all user inputs
- [ ] File uploads restricted and validated
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (output encoding)
- [ ] CSRF protection in place
- [ ] Session management secure
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] Error messages are generic
- [ ] No sensitive data in logs/responses
- [ ] Rate limiting implemented
- [ ] Sandbox restrictions on notebook execution
- [ ] LTI integration properly validated

---

## Reporting Findings

When you discover a vulnerability, document:
1. **Vulnerability Name & Type**
2. **Severity** (Critical/High/Medium/Low)
3. **Affected Endpoint/Component**
4. **Steps to Reproduce**
5. **Proof of Concept** (screenshots, requests)
6. **Impact** (what can an attacker do?)
7. **Remediation Recommendations**

### Severity Guidelines:
- **Critical**: Remote code execution, SQL injection with data access, authentication bypass
- **High**: Privilege escalation, stored XSS, sensitive data exposure
- **Medium**: CSRF, reflected XSS, information disclosure
- **Low**: Missing security headers, verbose errors, weak configurations

---

## Notes

- Always test in a **non-production environment** first
- Obtain proper **authorization** before testing
- **Document all findings** thoroughly
- **Retest** after fixes are applied
- Consider **automated scanning** as a complement, not replacement
- Stay updated on **OWASP Top 10** and emerging threats
