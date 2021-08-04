import os


def test_required_env_vars_presence(required_env_vars):
    assert all(var in os.environ for var in required_env_vars)
