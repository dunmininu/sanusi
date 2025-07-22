from accounts.services.oauth import OAuthService


def test_get_auth_url():
    url = OAuthService.get_auth_url("google", "state", "http://example.com/cb")
    assert "state=state" in url
    assert "client_id=" in url
