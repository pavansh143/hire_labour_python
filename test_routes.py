from app import app
import unittest

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_login_route(self):
        response = self.app.get('/login')
        print(f"Login status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_index_route(self):
        response = self.app.get('/')
        print(f"Index status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
