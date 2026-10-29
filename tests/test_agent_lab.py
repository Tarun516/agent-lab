import unittest

from agent_lab import list_experiments


class AgentLabTests(unittest.TestCase):
    def test_list_contains_sample_experiment(self):
        self.assertIn("hello-agent", list_experiments())


if __name__ == "__main__":
    unittest.main()
