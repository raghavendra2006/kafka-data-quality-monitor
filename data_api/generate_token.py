#!/usr/bin/env python3
"""
JWT Token Generator
====================
Helper script to generate JWT tokens for testing the Data Access API.

Usage:
    python generate_token.py --role analyst
    python generate_token.py --role admin
    python generate_token.py --role analyst --username test_user
"""

import argparse
import sys
import os
from datetime import timedelta

# Add parent to path so we can import from app
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import create_access_token


def main():
    parser = argparse.ArgumentParser(description="Generate JWT tokens for API testing")
    parser.add_argument(
        "--role",
        type=str,
        choices=["analyst", "admin"],
        default="analyst",
        help="Role to embed in the token (default: analyst)",
    )
    parser.add_argument(
        "--username",
        type=str,
        default="test_user",
        help="Username for the token (default: test_user)",
    )
    parser.add_argument(
        "--expiry",
        type=int,
        default=1440,
        help="Token expiry in minutes (default: 1440 = 24 hours)",
    )

    args = parser.parse_args()

    token = create_access_token(
        data={"sub": args.username, "role": args.role},
        expires_delta=timedelta(minutes=args.expiry),
    )

    print(f"\n{'='*60}")
    print(f"  JWT Token Generator")
    print(f"{'='*60}")
    print(f"  Username : {args.username}")
    print(f"  Role     : {args.role}")
    print(f"  Expiry   : {args.expiry} minutes")
    print(f"{'='*60}")
    print(f"\n  Token:\n")
    print(f"  {token}")
    print(f"\n  Usage:")
    print(f'  curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/sales/daily')
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
