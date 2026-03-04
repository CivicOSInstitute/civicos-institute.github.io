#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "phone-calls.jsonl"


def is_e164(num: str) -> bool:
    return bool(re.fullmatch(r"\+[1-9]\d{7,14}", num or ""))


def log_event(payload: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--from-number", default=os.getenv("TWILIO_FROM_NUMBER"))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--live", action="store_true")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).isoformat()

    if not is_e164(args.to):
        raise SystemExit("Invalid --to number. Use E.164, e.g. +15615551234")

    if not args.from_number or not is_e164(args.from_number):
        raise SystemExit("Missing/invalid --from-number (or TWILIO_FROM_NUMBER)")

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    tok = os.getenv("TWILIO_AUTH_TOKEN")
    missing = [k for k, v in {
        "TWILIO_ACCOUNT_SID": sid,
        "TWILIO_AUTH_TOKEN": tok,
    }.items() if not v]

    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")

    payload = {
        "timestamp": ts,
        "provider": "twilio",
        "to_number": args.to,
        "from_number": args.from_number,
        "mode": "live" if args.live else "dry-run",
        "status": "preview" if not args.live else "pending"
    }

    if not args.live:
        payload["preview"] = {
            "twiml": f"<Response><Say>{args.message}</Say></Response>"
        }
        log_event(payload)
        print(json.dumps(payload, indent=2))
        return

    # Lazy import to avoid dependency requirement for dry-runs.
    from twilio.rest import Client  # type: ignore

    client = Client(sid, tok)
    call = client.calls.create(
        twiml=f"<Response><Say>{args.message}</Say></Response>",
        to=args.to,
        from_=args.from_number,
    )

    payload.update({"status": "queued", "call_sid": call.sid})
    log_event(payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
