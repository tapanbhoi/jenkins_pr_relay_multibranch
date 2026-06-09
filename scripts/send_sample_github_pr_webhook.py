#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a signed sample GitHub PR webhook.")
    parser.add_argument("--url", default="http://localhost:8000/webhooks/github")
    parser.add_argument("--secret", required=True)
    parser.add_argument("--pr", type=int, default=1)
    parser.add_argument("--action", default="opened")
    args = parser.parse_args()

    payload = {
        "action": args.action,
        "repository": {"full_name": "example-org/example-repo"},
        "pull_request": {
            "number": args.pr,
            "head": {"ref": "feature/demo", "sha": "abc1234"},
            "base": {"ref": "main"},
        },
    }
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(args.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    request = Request(
        args.url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature}",
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        print(response.status)
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
