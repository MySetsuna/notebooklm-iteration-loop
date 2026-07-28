#!/usr/bin/env python3
"""Save NLM credentials from an already authenticated external CDP browser.

Prints only non-secret metadata. Run with notebooklm-mcp-cli's virtualenv Python.
"""

from __future__ import annotations

import argparse
import json

from notebooklm_tools.core.auth import get_auth_manager
from notebooklm_tools.utils.cdp import extract_cookies_via_existing_cdp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cdp-url", required=True)
    parser.add_argument("--profile", default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacing a profile that belongs to a different account.",
    )
    args = parser.parse_args()

    result = extract_cookies_via_existing_cdp(
        cdp_url=args.cdp_url,
        wait_for_login=False,
    )
    auth = get_auth_manager(args.profile)
    auth.save_profile(
        cookies=result["cookies"],
        csrf_token=result.get("csrf_token", ""),
        session_id=result.get("session_id", ""),
        email=result.get("email", ""),
        force=args.force,
        build_label=result.get("build_label", ""),
    )
    print(
        json.dumps(
            {
                "saved": True,
                "profile": auth.profile_name,
                "cookie_count": len(result["cookies"]),
                "csrf_present": bool(result.get("csrf_token")),
                "session_present": bool(result.get("session_id")),
            }
        )
    )


if __name__ == "__main__":
    main()
