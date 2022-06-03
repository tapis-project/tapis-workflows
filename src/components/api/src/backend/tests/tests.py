from django.test import TestCase

from backend.conf.constants import DJANGO_TAPIS_TOKEN_HEADER
from backend.utils.fixture_loader import fixture_loader as load

class URLTests(TestCase):
    def test_urls_unauth(self):
        res = self.client.get("/healthcheck/")
        self.assertEqual(res.status_code, 200)

class URLTestsAuthenticated(TestCase):
    def test_urls_auth(self):
        res = self.client.post(
            "/auth/",
            data={
                "username": "testuser2",
                "password": "testuser2" 
            }
        )

        self.jwt = res.result.jwt

        self.headers = {
            DJANGO_TAPIS_TOKEN_HEADER: self.jwt,
            "Content-Type": "application/json"
        }

        client = {
            "get": self.client.get,
            "post": self.client.post,
            "patch": self.client.patch,
            "put": self.client.put,
            "delete": self.client.delete
        }

        tests = [
            (
                "/groups/", [
                    ("get", 200),
                    ("post", 200, load("group"))
                ]
            ),
            (
                "/groups/g1", [
                    ("get", 200)
                ]
            ),
            (
                "/groups/g1/users", [
                    ("get", 200)
                ]
            ),
        ]

        for test in tests:
            url = test[0]
            assertions = test[1]
            for assertion in assertions:
                (method, status_code) = assertion
                res = client[method](
                    url,
                    **self.headers,
                    data=None if len(assertion) < 3 else assertion[2]
                )

                self.assertEqual(
                    res.status_code,
                    status_code,
                    msg=f"Test: [{method.upper()}] {url}",
                )