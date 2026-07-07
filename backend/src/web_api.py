"""Backward-compatible HTTP API entrypoint."""
from .api.app import init_app, main


if __name__ == "__main__":
    main()
