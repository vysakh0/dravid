import pytest
import sys


def main():
    sys.exit(pytest.main(["-v", "src"]))


if __name__ == "__main__":
    main()
