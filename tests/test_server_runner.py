import unittest
from unittest.mock import patch, call
import sys
import server_runner

class TestServerRunner(unittest.TestCase):

    @patch('waitress.serve')
    @patch.dict('sys.modules', {'sys': type(sys)('frozen')})
    def test_waitress_serve_used_when_frozen(self, mock_waitress_serve):
        # Mock sys.frozen to be True
        sys.frozen = True

        # Call the run function
        server_runner.run()

        # Assert waitress.serve was called
        self.assertTrue(mock_waitress_serve.called)

    @patch('uvicorn.run')
    @patch.dict('sys.modules', {'sys': type(sys)('frozen')})
    def test_uvicorn_run_used_when_not_frozen(self, mock_uvicorn_run):
        # Mock sys.frozen to be False
        sys.frozen = False

        # Call the run function
        server_runner.run()

        # Assert uvicorn.run was called
        self.assertTrue(mock_uvicorn_run.called)

if __name__ == '__main__':
    unittest.main()