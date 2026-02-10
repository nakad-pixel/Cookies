import pytest

from src.cleanup import SecureWiper, redact_cookies_from_log, redact_sensitive


class TestSecureWiper:
    def test_wipe_bytes_overwrites_data(self):
        """Test that wipe_bytes overwrites data."""
        data = bytearray(b"sensitive data here")
        original = bytes(data)
        SecureWiper.wipe_bytes(data)
        # After wiping, data should be zeros
        assert bytes(data) != original
        assert data == bytearray(b"\x00" * len(original))

    def test_wipe_object_clears_fields(self):
        """Test that wipe_object clears sensitive fields."""
        class TestObject:
            def __init__(self):
                self.value = "secret"
                self.password = "pass123"
                self.normal = "keep this"

        obj = TestObject()
        SecureWiper.wipe_object(obj)

        assert obj.value is None
        assert obj.password is None
        assert obj.normal == "keep this"

    def test_clear_temp_files_removes_matching_files(self, tmp_path, monkeypatch):
        """Test that clear_temp_files removes matching files."""
        import tempfile

        # Create temp files
        temp_file1 = tmp_path / "cookie_123.txt"
        temp_file2 = tmp_path / "cookie_456.txt"
        other_file = tmp_path / "other_789.txt"

        temp_file1.write_text("test")
        temp_file2.write_text("test")
        other_file.write_text("test")

        # Monkeypatch gettempdir
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

        count = SecureWiper.clear_temp_files(pattern="cookie_*")

        assert count == 2
        assert not temp_file1.exists()
        assert not temp_file2.exists()
        assert other_file.exists()

    def test_force_gc_does_not_raise(self):
        """Test that force_gc runs without error."""
        SecureWiper.force_gc()  # Should not raise


class TestRedactSensitive:
    def test_redact_long_string(self):
        """Test redaction of a long string."""
        value = "super-secret-api-key-12345"
        result = redact_sensitive(value, visible_chars=4)
        assert result == "supe***2345"

    def test_redact_short_string(self):
        """Test redaction of a short string returns fully redacted."""
        value = "abc"
        result = redact_sensitive(value)
        assert result == "[REDACTED]"

    def test_redact_empty_string(self):
        """Test redaction of empty string."""
        result = redact_sensitive("")
        assert result == "[REDACTED]"

    def test_redact_none(self):
        """Test redaction of None."""
        result = redact_sensitive(None)
        assert result == "[REDACTED]"


class TestRedactCookiesFromLog:
    def test_redact_cookie_header(self):
        """Test redaction of Cookie header."""
        message = "Request headers: Cookie: session_id=abc123; auth=xyz789"
        result = redact_cookies_from_log(message)
        assert "session_id=abc123" not in result
        assert "[REDACTED]" in result

    def test_redact_authorization_header(self):
        """Test redaction of Authorization header."""
        message = "Authorization: Bearer secret-token-12345"
        result = redact_cookies_from_log(message)
        assert "secret-token-12345" not in result
        assert "[REDACTED]" in result

    def test_redact_json_value(self):
        """Test redaction of JSON value field."""
        message = '{"name":"session","value":"secret123","domain":"example.com"}'
        result = redact_cookies_from_log(message)
        assert "secret123" not in result
        assert '"value":"[REDACTED]"' in result

    def test_redact_password_in_query(self):
        """Test redaction of password in query string."""
        message = "POST /login?username=user&password=secret123&remember=true"
        result = redact_cookies_from_log(message)
        assert "secret123" not in result
        assert "password=[REDACTED]" in result

    def test_redact_token_in_query(self):
        """Test redaction of token in query string."""
        message = "GET /api?token=abc123&action=test"
        result = redact_cookies_from_log(message)
        assert "abc123" not in result
        assert "token=[REDACTED]" in result

    def test_leave_safe_content_unchanged(self):
        """Test that safe content is not modified."""
        message = "Repository example/repo processed successfully"
        result = redact_cookies_from_log(message)
        assert result == message
