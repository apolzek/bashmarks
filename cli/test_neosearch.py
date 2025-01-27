import unittest
import os
import json
from unittest.mock import patch, mock_open
from neosearch import validate_repository, load_data_from_file, filter_data, truncate_description

class TestRepositories(unittest.TestCase):

    # def test_validate_repository_valid_url(self):
    #     with patch('requests.get') as mocked_get:
    #         mocked_get.return_value.status_code = 200
    #         mocked_get.return_value.json.return_value = {"key": "value"}
    #         is_valid, message = validate_repository("https://example.com/data.json")
    #         self.assertTrue(is_valid)
    #         self.assertEqual(message, "OK")

    # def test_validate_repository_invalid_url(self):
    #     with patch('requests.get') as mocked_get:
    #         mocked_get.return_value.status_code = 404
    #         is_valid, message = validate_repository("https://example.com/invalid.json")
    #         self.assertFalse(is_valid)
    #         self.assertIn("Invalid format", message)

    def test_validate_repository_valid_local_file(self):
        mock_data = '{"key": "value"}'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            is_valid, message = validate_repository(".files/private.json")
            self.assertTrue(is_valid)
            self.assertEqual(message, "OK")

    def test_validate_repository_invalid_local_file(self):
        with patch('os.path.exists', return_value=False):
            is_valid, message = validate_repository("nonexistent_file.json")
            self.assertFalse(is_valid)
            self.assertEqual(message, "File not found")

    def test_load_data_from_file_valid(self):
        mock_data = '{"key": "value"}'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            data = load_data_from_file(".files/private.json")
            self.assertEqual(data, {"key": "value"})

    def test_load_data_from_file_invalid(self):
        mock_data = 'invalid json'
        with patch('builtins.open', mock_open(read_data=mock_data)):
            data = load_data_from_file(".files/err.json")
            self.assertIsNone(data)

    def test_filter_data_by_keyword(self):
        data = [
            {"url": "http://example.com", "description": "Example site", "category": "example"},
            {"url": "http://another.com", "description": "Another site", "category": "another"}
        ]
        filtered = filter_data(data, keyword="example")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["url"], "http://example.com")

    def test_filter_data_by_field(self):
        data = [
            {"url": "http://example.com", "description": "Example site", "category": "example"},
            {"url": "http://another.com", "description": "Another site", "category": "another"}
        ]
        filtered = filter_data(data, keyword="example", field="category")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["url"], "http://example.com")

    # def test_truncate_description(self):
    #     description = "This is a very long description that needs to be truncated"
    #     truncated = truncate_description(description, length=20)
    #     self.assertEqual(truncated, "This is a very long...")

if __name__ == '__main__':
    unittest.main()