#!/usr/bin/env python3
import sys
import json
import re

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)

        payload = json.loads(input_data)

        if payload.get("toolName") == "run_command":
            args = payload.get("arguments", {})
            cmd = args.get("CommandLine", "")

            # Simple check for destructive commands
            destructive_patterns = [
                r"rm\s+-r[fF]?\s+/",
                r"rm\s+-r[fF]?\s+\*",
                r"rm\s+-r[fF]?\s+\.",
                r">\s*/dev/sda",
                r"mkfs",
                r"dd\s+if=.*of=/dev"
            ]

            for pattern in destructive_patterns:
                if re.search(pattern, cmd):
                    print(f"Blocked: Destructive command detected matching '{pattern}'", file=sys.stderr)
                    sys.exit(1)

        sys.exit(0)
    except Exception as e:
        print(f"Error validating tool call: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
