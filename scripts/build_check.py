#!/usr/bin/env python3
"""Build check script for the SIP project."""

import os


def main() -> None:
    """Check that build artifacts exist and are valid."""
    dist_files = os.listdir("dist")
    wheel_files = [f for f in dist_files if f.endswith(".whl")]
    tar_files = [f for f in dist_files if f.endswith(".tar.gz")]

    if not wheel_files:
        raise Exception("No wheel file found")
    if not tar_files:
        raise Exception("No source distribution found")

    print(f"✅ Built {len(wheel_files)} wheel(s) and {len(tar_files)} source distribution(s)")
    for f in dist_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
