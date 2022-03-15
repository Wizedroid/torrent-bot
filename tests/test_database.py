import unittest
from src.data import TBDatabase


class TestTBDatabase(unittest.TestCase):
    def test_create_schema(self):
        db = TBDatabase('test.db')
        db.create_schema()
        db.close()

if __name__ == '__main__':
    unittest.main()
