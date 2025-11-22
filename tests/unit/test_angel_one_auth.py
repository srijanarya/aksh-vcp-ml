"""
Unit tests for Angel One Authentication

Following TDD approach:
1. RED: Write failing tests first
2. GREEN: Make tests pass
3. REFACTOR: Improve code

Test Coverage Target: 100% (critical component)
"""

import pytest
from datetime import datetime
import pyotp


class TestAngelOneAuthInitialization:
    """Test AngelOneClient initialization"""

    def test_client_initialization_with_credentials(self):
        """Test client initializes with valid credentials"""
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_api_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="TESTSECRET"
        )

        assert client.api_key == "test_api_key"
        assert client.client_id == "TEST123"
        assert client.mpin == "1234"
        assert client.totp_secret == "TESTSECRET"
        assert client.session_token is None  # Not authenticated yet

    def test_client_initialization_from_env(self, monkeypatch):
        """Test client initializes from environment variables"""
        from src.data.angel_one_client import AngelOneClient

        # Set environment variables
        monkeypatch.setenv("ANGEL_API_KEY", "env_api_key")
        monkeypatch.setenv("ANGEL_CLIENT_ID", "ENV123")
        monkeypatch.setenv("ANGEL_MPIN", "5678")
        monkeypatch.setenv("ANGEL_TOTP_SECRET", "ENVSECRET")

        client = AngelOneClient.from_env()

        assert client.api_key == "env_api_key"
        assert client.client_id == "ENV123"
        assert client.mpin == "5678"
        assert client.totp_secret == "ENVSECRET"

    def test_client_initialization_missing_api_key(self):
        """Test client raises error when API key missing"""
        from src.data.angel_one_client import AngelOneClient

        with pytest.raises(ValueError, match="API key is required"):
            AngelOneClient(
                api_key=None,
                client_id="TEST123",
                mpin="1234",
                totp_secret="SECRET"
            )

    def test_client_initialization_missing_client_id(self):
        """Test client raises error when client ID missing"""
        from src.data.angel_one_client import AngelOneClient

        with pytest.raises(ValueError, match="Client ID is required"):
            AngelOneClient(
                api_key="test_key",
                client_id=None,
                mpin="1234",
                totp_secret="SECRET"
            )

    def test_client_initialization_missing_mpin(self):
        """Test client raises error when MPIN missing"""
        from src.data.angel_one_client import AngelOneClient

        with pytest.raises(ValueError, match="MPIN is required"):
            AngelOneClient(
                api_key="test_key",
                client_id="TEST123",
                mpin=None,
                totp_secret="SECRET"
            )

    def test_client_initialization_missing_totp_secret(self):
        """Test client raises error when TOTP secret missing"""
        from src.data.angel_one_client import AngelOneClient

        with pytest.raises(ValueError, match="TOTP secret is required"):
            AngelOneClient(
                api_key="test_key",
                client_id="TEST123",
                mpin="1234",
                totp_secret=None
            )


class TestTOTPGeneration:
    """Test TOTP (Time-based One-Time Password) generation"""

    def test_generate_totp(self):
        """Test TOTP generation from secret"""
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"  # Standard test secret
        )

        totp = client.generate_totp()

        # TOTP should be 6 digits
        assert len(totp) == 6
        assert totp.isdigit()

    def test_totp_changes_over_time(self):
        """Test TOTP is time-based (changes every 30 seconds)"""
        from src.data.angel_one_client import AngelOneClient
        import time

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        # Note: This test may be flaky near 30-second boundaries
        # In production, we'd mock time
        totp1 = client.generate_totp()
        time.sleep(0.1)
        totp2 = client.generate_totp()

        # Within same 30-second window, should be same
        assert totp1 == totp2

    def test_totp_validation(self):
        """Test TOTP can be validated"""
        from src.data.angel_one_client import AngelOneClient

        secret = "JBSWY3DPEHPK3PXP"
        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret=secret
        )

        totp = client.generate_totp()

        # Verify using pyotp directly
        totp_obj = pyotp.TOTP(secret)
        assert totp_obj.verify(totp)


class TestAngelOneAuthentication:
    """Test Angel One API authentication flow"""

    def test_authenticate_success(self, mocker):
        """Test successful authentication"""
        from src.data.angel_one_client import AngelOneClient

        # Mock the SmartAPI response
        mock_smartapi = mocker.Mock()
        mock_smartapi.generateSession.return_value = {
            'status': True,
            'message': 'SUCCESS',
            'data': {
                'jwtToken': 'test_jwt_token_12345',
                'refreshToken': 'test_refresh_token_67890',
                'feedToken': 'test_feed_token'
            }
        }

        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        result = client.authenticate()

        # Verify authentication succeeded
        assert result is True
        assert client.session_token == 'test_jwt_token_12345'
        assert client.refresh_token == 'test_refresh_token_67890'
        assert client.is_authenticated is True

        # Verify SmartAPI was called correctly with keyword arguments
        mock_smartapi.generateSession.assert_called_once()
        call_kwargs = mock_smartapi.generateSession.call_args[1]
        assert call_kwargs['clientCode'] == "TEST123"
        assert call_kwargs['password'] == "1234"
        assert 'totp' in call_kwargs

    def test_authenticate_failure(self, mocker):
        """Test authentication failure"""
        from src.data.angel_one_client import AngelOneClient

        # Mock failed authentication
        mock_smartapi = mocker.Mock()
        mock_smartapi.generateSession.return_value = {
            'status': False,
            'message': 'Invalid credentials',
            'data': None
        }

        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="wrong_key",
            client_id="WRONG123",
            mpin="0000",
            totp_secret="JBSWY3DPEHPK3PXP"  # Valid base32 secret
        )

        result = client.authenticate()

        # Verify authentication failed
        assert result is False
        assert client.session_token is None
        assert client.is_authenticated is False

    def test_authenticate_network_error(self, mocker):
        """Test authentication handles network errors"""
        from src.data.angel_one_client import AngelOneClient
        import requests

        # Mock network error
        mock_smartapi = mocker.Mock()
        mock_smartapi.generateSession.side_effect = requests.ConnectionError(
            "Network unreachable"
        )

        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"  # Valid base32 secret
        )

        with pytest.raises(requests.ConnectionError):
            client.authenticate()

    def test_authenticate_timeout(self, mocker):
        """Test authentication handles timeouts"""
        from src.data.angel_one_client import AngelOneClient
        import requests

        # Mock timeout
        mock_smartapi = mocker.Mock()
        mock_smartapi.generateSession.side_effect = requests.Timeout(
            "Request timeout"
        )

        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"  # Valid base32 secret
        )

        with pytest.raises(requests.Timeout):
            client.authenticate()


class TestSessionManagement:
    """Test session token management"""

    def test_is_authenticated_property(self, mocker):
        """Test is_authenticated property"""
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="SECRET"
        )

        # Before authentication
        assert client.is_authenticated is False

        # After setting session token
        client.session_token = "test_token"
        assert client.is_authenticated is True

        # After clearing session
        client.session_token = None
        assert client.is_authenticated is False

    def test_logout_clears_session(self, mocker):
        """Test logout clears session tokens"""
        from src.data.angel_one_client import AngelOneClient

        mock_smartapi = mocker.Mock()
        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="SECRET"
        )

        # Set authenticated state
        client.session_token = "test_token"
        client.refresh_token = "refresh_token"

        # Logout
        client.logout()

        # Verify session cleared
        assert client.session_token is None
        assert client.refresh_token is None
        assert client.is_authenticated is False

    def test_refresh_session(self, mocker):
        """Test session refresh"""
        from src.data.angel_one_client import AngelOneClient

        mock_smartapi = mocker.Mock()
        mock_smartapi.renewAccessToken.return_value = {
            'status': True,
            'data': {
                'jwtToken': 'new_jwt_token',
                'refreshToken': 'new_refresh_token'
            }
        }

        mocker.patch(
            'src.data.angel_one_client.SmartConnect',
            return_value=mock_smartapi
        )

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"  # Valid base32 secret
        )

        # Set up _smart_api and refresh_token (simulating authenticated state)
        client._smart_api = mock_smartapi
        client.refresh_token = "old_refresh_token"

        # Refresh session
        result = client.refresh_session()

        assert result is True
        assert client.session_token == 'new_jwt_token'
        assert client.refresh_token == 'new_refresh_token'

    def test_refresh_session_no_refresh_token(self, mocker):
        """Test refresh session fails when no refresh token"""
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        # No refresh token set
        result = client.refresh_session()

        assert result is False

    def test_refresh_session_api_failure(self, mocker):
        """Test refresh session handles API failure"""
        from src.data.angel_one_client import AngelOneClient

        mock_smartapi = mocker.Mock()
        mock_smartapi.renewAccessToken.return_value = {
            'status': False,
            'message': 'Invalid refresh token'
        }

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        client._smart_api = mock_smartapi
        client.refresh_token = "invalid_token"

        result = client.refresh_session()

        assert result is False

    def test_refresh_session_exception(self, mocker):
        """Test refresh session handles exceptions"""
        from src.data.angel_one_client import AngelOneClient

        mock_smartapi = mocker.Mock()
        mock_smartapi.renewAccessToken.side_effect = Exception("Network error")

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )

        client._smart_api = mock_smartapi
        client.refresh_token = "test_token"

        result = client.refresh_session()

        assert result is False


class TestCredentialsFromEnvFile:
    """Test loading credentials from .env.angel file"""

    def test_load_from_angel_env_file(self, tmp_path, monkeypatch):
        """Test loading credentials from .env.angel"""
        from src.data.angel_one_client import AngelOneClient

        # Create temporary .env.angel file
        env_file = tmp_path / ".env.angel"
        env_file.write_text("""
export ANGEL_API_KEY="yip3kpG2"
export ANGEL_CLIENT_ID="S692691"
export ANGEL_MPIN="8383"
export ANGEL_TOTP_SECRET="X7TPG2AANT6UYOVJVKCQIR2CMM="
        """)

        # Point to temp file
        monkeypatch.setenv("ANGEL_ENV_FILE", str(env_file))

        client = AngelOneClient.from_env_file(str(env_file))

        assert client.api_key == "yip3kpG2"
        assert client.client_id == "S692691"
        assert client.mpin == "8383"
        assert client.totp_secret == "X7TPG2AANT6UYOVJVKCQIR2CMM="

    def test_load_from_default_angel_env_location(self, tmp_path, monkeypatch):
        """Test loading from default location"""
        from src.data.angel_one_client import AngelOneClient

        # Create .env.angel in project root
        project_root = tmp_path
        env_file = project_root / ".env.angel"
        env_file.write_text("""
export ANGEL_API_KEY="default_key"
export ANGEL_CLIENT_ID="DEFAULT123"
export ANGEL_MPIN="9999"
export ANGEL_TOTP_SECRET="DEFAULTSECRET"
        """)

        # Mock project root
        monkeypatch.chdir(project_root)

        client = AngelOneClient.from_env_file()

        assert client.api_key == "default_key"


class TestRealCredentialsIntegration:
    """Integration tests with real Angel One credentials (if available)"""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Integration test - run manually with real credentials")
    def test_real_authentication(self):
        """Test authentication with real credentials (integration test)"""
        from src.data.angel_one_client import AngelOneClient

        # Load real credentials from actual .env.angel
        client = AngelOneClient.from_env_file(
            "/Users/srijan/vcp_clean_test/vcp/.env.angel"
        )

        # Attempt real authentication
        result = client.authenticate()

        # This should succeed if credentials are valid
        assert result is True
        assert client.is_authenticated is True
        assert client.session_token is not None

        # Clean up
        client.logout()
