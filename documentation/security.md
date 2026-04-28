# General Security Flow
1. User logs in --> Gets JWT token
2. Client sends the toekn in headers
3. FAST API extracts tokens in OAuth2 scheme
4. Token is decoded --> email is extracted
5. User id fetched from DB
6. Role is checked (if required)
7. Request is allowed/rejected



A bearer token is a cryptic string used in OAuth2.0 and API authentication to grant access to protected resources.

