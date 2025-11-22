# SHORT-001: Angel One Authentication & Token Management

**Parent**: FX-001 (Data Ingestion)
**Estimated Effort**: 4 hours
**Priority**: HIGH
**Dependencies**: None

---

## Objective

Implement secure authentication with Angel One SmartAPI using API key, client ID, password, and TOTP, with automatic token refresh.

---

## Acceptance Criteria

- [ ] AC-1: Successfully authenticate with Angel One using valid credentials
- [ ] AC-2: Store JWT token with 24-hour expiry
- [ ] AC-3: Auto-refresh token before expiry
- [ ] AC-4: Handle authentication failures gracefully
- [ ] AC-5: Generate TOTP using pyotp library
- [ ] AC-6: Log all authentication attempts

---

## Test Cases (Write FIRST)

### TC-1: Successful Authentication

```python
def test_successful_authentication(mocker):
    """Test successful login with valid credentials"""

    # Mock SmartConnect.generateSession
    mock_session = mocker.patch(
        "SmartApi.SmartConnect.generateSession",
        return_value={
            "status": True,
            "data": {
                "jwtToken": "mock_jwt_token",
                "refreshToken": "mock_refresh_token",
                "feedToken": "mock_feed_token",
            },
        },
    )

    # Mock TOTP generation
    mocker.patch("pyotp.TOTP.now", return_value="123456")

    # Initialize authenticator
    auth = AngelOneAuthenticator(
        api_key="test_api_key",
        client_id="test_client_id",
        password="test_password",
        totp_secret="test_totp_secret",
    )

    # Authenticate
    auth.login()

    # Assertions
    assert auth.is_authenticated is True
    assert auth.jwt_token == "mock_jwt_token"
    assert auth.refresh_token == "mock_refresh_token"

    # Verify generateSession was called with correct params
    mock_session.assert_called_once_with(
        clientCode="test_client_id",
        password="test_password",
        totp="123456",
    )
```

### TC-2: Authentication Failure

```python
def test_authentication_failure(mocker):
    """Test handling of authentication failures"""

    # Mock failed authentication
    mocker.patch(
        "SmartApi.SmartConnect.generateSession",
        return_value={
            "status": False,
            "message": "Invalid credentials",
        },
    )

    mocker.patch("pyotp.TOTP.now", return_value="123456")

    auth = AngelOneAuthenticator(...)

    # Attempt login (should raise exception)
    with pytest.raises(AuthenticationError) as exc_info:
        auth.login()

    assert "Invalid credentials" in str(exc_info.value)
    assert auth.is_authenticated is False
```

### TC-3: Token Expiry Check

```python
def test_token_expiry_check():
    """Test token expiry detection"""

    auth = AngelOneAuthenticator(...)

    # Manually set token with expired time
    auth.jwt_token = "expired_token"
    auth.token_expiry = datetime.now() - timedelta(hours=1)
    auth.is_authenticated = True

    # Check if token is expired
    is_valid = auth.is_token_valid()

    assert is_valid is False
```

### TC-4: Auto Token Refresh

```python
def test_auto_token_refresh(mocker):
    """Test automatic token refresh before expiry"""

    # Mock login
    mock_login = mocker.patch.object(
        AngelOneAuthenticator, "login"
    )

    auth = AngelOneAuthenticator(...)

    # Set token that expires in 1 minute
    auth.jwt_token = "old_token"
    auth.token_expiry = datetime.now() + timedelta(minutes=1)
    auth.is_authenticated = True

    # Check authentication (should trigger refresh)
    auth.check_and_refresh()

    # Verify login was called to refresh
    mock_login.assert_called_once()
```

### TC-5: TOTP Generation

```python
def test_totp_generation():
    """Test TOTP generation from secret"""

    auth = AngelOneAuthenticator(
        totp_secret="JBSWY3DPEHPK3PXP",  # Example secret
        ...
    )

    totp_code = auth.generate_totp()

    # TOTP should be 6 digits
    assert len(totp_code) == 6
    assert totp_code.isdigit()
```

---

## Implementation

### Class: `AngelOneAuthenticator`

```python
# data/angel_one_auth.py
from SmartApi import SmartConnect
import pyotp
from datetime import datetime, timedelta
from typing import Optional
import logging

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class AngelOneAuthenticator:
    """
    Handle Angel One authentication and token management

    Responsibilities:
    - Authenticate with Angel One SmartAPI
    - Manage JWT token lifecycle
    - Auto-refresh tokens before expiry
    - Generate TOTP for 2FA
    """

    def __init__(
        self,
        api_key: str,
        client_id: str,
        password: str,
        totp_secret: str,
    ):
        """
        Initialize authenticator

        Args:
            api_key: Angel One API key
            client_id: Client ID (login ID)
            password: Account password
            totp_secret: TOTP secret for 2FA
        """
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret

        self.logger = logging.getLogger(__name__)

        # SmartAPI client
        self.smart_api = SmartConnect(api_key=api_key)

        # Authentication state
        self.jwt_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.feed_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.is_authenticated = False

    def login(self):
        """
        Authenticate with Angel One

        Raises:
            AuthenticationError: If authentication fails
        """
        self.logger.info("Authenticating with Angel One...")

        try:
            # Generate TOTP
            totp = self.generate_totp()

            # Login
            session = self.smart_api.generateSession(
                clientCode=self.client_id,
                password=self.password,
                totp=totp,
            )

            if not session["status"]:
                raise AuthenticationError(
                    f"Login failed: {session.get('message', 'Unknown error')}"
                )

            # Store tokens
            self.jwt_token = session["data"]["jwtToken"]
            self.refresh_token = session["data"]["refreshToken"]
            self.feed_token = session["data"]["feedToken"]

            # Token valid for 24 hours (conservative: 23 hours)
            self.token_expiry = datetime.now() + timedelta(hours=23)

            self.is_authenticated = True

            self.logger.info(
                f"Angel One login successful. "
                f"Token expires: {self.token_expiry.strftime('%Y-%m-%d %H:%M')}"
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(str(e))

    def generate_totp(self) -> str:
        """
        Generate TOTP code from secret

        Returns:
            6-digit TOTP code
        """
        totp = pyotp.TOTP(self.totp_secret)
        return totp.now()

    def is_token_valid(self) -> bool:
        """
        Check if token is still valid

        Returns:
            True if token is valid, False otherwise
        """
        if not self.is_authenticated:
            return False

        if not self.token_expiry:
            return False

        # Check if expired
        return datetime.now() < self.token_expiry

    def check_and_refresh(self):
        """Check token validity and refresh if needed"""

        if not self.is_token_valid():
            self.logger.warning("Token expired or invalid. Re-authenticating...")
            self.login()
        elif self.token_expiry and (
            datetime.now() >= self.token_expiry - timedelta(minutes=30)
        ):
            # Refresh if within 30 minutes of expiry
            self.logger.info(
                "Token expiring soon. Refreshing preemptively..."
            )
            self.login()
```

---

## Implementation Checklist

- [ ] Create `data/angel_one_auth.py`
- [ ] Install dependencies: `pip install smartapi-python pyotp`
- [ ] Write all 5 test cases first
- [ ] Run tests (should FAIL)
- [ ] Implement `AngelOneAuthenticator` class
- [ ] Implement `login()` method
- [ ] Implement `generate_totp()` method
- [ ] Implement `is_token_valid()` method
- [ ] Implement `check_and_refresh()` method
- [ ] Run tests (should PASS)
- [ ] Verify code coverage ≥ 95%
- [ ] Add logging statements
- [ ] Add docstrings
- [ ] Code review

---

## Dependencies

**External**:
- `smartapi-python`: Angel One SDK
- `pyotp`: TOTP generation

**Internal**:
- None (foundation task)

---

## Definition of Done

- [ ] All 5 test cases passing
- [ ] Code coverage ≥ 95%
- [ ] Handles authentication failures gracefully
- [ ] Auto-refresh working
- [ ] Logging implemented
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Manual test with real Angel One credentials successful

---

## Testing Notes

**Unit Testing**:
- Mock all `SmartConnect.generateSession` calls
- Mock `pyotp.TOTP.now()` to return predictable values
- Test both success and failure paths

**Integration Testing**:
- Use Angel One sandbox/testnet (if available)
- Or use real credentials with caution
- Verify actual JWT token is received

**Security Notes**:
- Never commit credentials to version control
- Use environment variables for sensitive data
- Consider using secrets manager in production

---

**Status**: ✅ Ready for Implementation
**Estimated Completion**: 4 hours
**Next**: SHORT-002 (Angel One OHLCV Fetcher)
