import os
from typing import List


def test_required_env_vars_presence(required_env_vars: List[str]) -> None:
    assert all(var in os.environ for var in required_env_vars)
