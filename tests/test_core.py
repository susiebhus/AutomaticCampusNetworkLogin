import unittest

from njust_campus_login.core import (
    DEFAULT_LOGIN_URL,
    Credentials,
    LoginConfig,
    is_online,
    login,
)


class FakeResponse:
    def __init__(self, status_code: int, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text
        self.ok = 200 <= status_code < 300


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.get_calls = []
        self.post_calls = []

    def get(self, url: str, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.response

    def post(self, url: str, **kwargs):
        self.post_calls.append((url, kwargs))
        return self.response


class CoreTest(unittest.TestCase):
    def test_default_connectivity_check_requires_204(self) -> None:
        self.assertTrue(is_online(session=FakeSession(FakeResponse(204)), emit=lambda _: None))
        self.assertFalse(is_online(session=FakeSession(FakeResponse(200)), emit=lambda _: None))

    def test_custom_connectivity_check_accepts_2xx(self) -> None:
        self.assertTrue(
            is_online("https://example.com", session=FakeSession(FakeResponse(200)), emit=lambda _: None)
        )

    def test_login_posts_expected_payload_and_headers(self) -> None:
        session = FakeSession(FakeResponse(200, '{"success":true}'))
        result = login(
            Credentials("u", "p"),
            LoginConfig(warmup_portal=False),
            session=session,
            emit=lambda _: None,
        )

        self.assertTrue(result.ok)
        self.assertEqual(len(session.post_calls), 1)
        url, kwargs = session.post_calls[0]
        self.assertEqual(url, DEFAULT_LOGIN_URL)
        self.assertEqual(kwargs["json"], {"domain": "default", "username": "u", "password": "p"})
        self.assertEqual(kwargs["headers"]["Origin"], "http://10.132.100.104")
        self.assertEqual(kwargs["headers"]["Referer"], "http://10.132.100.104/")


if __name__ == "__main__":
    unittest.main()
