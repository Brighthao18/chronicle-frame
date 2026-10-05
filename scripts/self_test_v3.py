#!/usr/bin/env python3
"""Compatibility alias: the v3 smoke test is superseded by the 3.1 behavioral suite."""

from self_test_v31 import main

if __name__ == "__main__":
    raise SystemExit(main())
