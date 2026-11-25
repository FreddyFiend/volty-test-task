"""Run the lead-qualifier test scenarios against the live Volty agent, in the Sandbox.

Each scenario is a short conversation from a fresh synthetic contact (replies never leave Volty).
After the last turn it reads the conversation, the agent's tool calls and the contact record,
checks them against the scenario's expectations, and writes a Markdown report.

Usage:  python tests/run_tests.py [T01 T05 ...]      (no ids = every scenario)
Needs:  the volty CLI signed in to prod; VOLTY_ORG below names the org.
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ORG = "z79qt1cgu7bp"
HERE = Path(__file__).resolve().parent
VOLTY = str(Path.home() / ".bun" / "bin" / ("volty.exe" if os.name == "nt" else "volty"))
ENV = {**os.environ, "VOLTY_ENV": "prod", "VOLTY_ORG": ORG, "MSYS_NO_PATHCONV": "1"}
# Volty's three ways to put a person on a conversation: assign-team (the team is asked to claim it),
# hand-to-team (only when the contact asks for a person) and consult (ask one staff member a question).
HANDOFF_OPS = ("conversations assign-team", "conversations hand-to-team", "consult", "involve")


def volty(*args, want_json=True):
    cmd = [VOLTY, *args] + (["--json"] if want_json else [])
    out = subprocess.run(cmd, env=ENV, capture_output=True, text=True, encoding="utf-8", timeout=180)
    if out.returncode != 0:
        raise RuntimeError(f"volty {' '.join(args)} failed: {out.stderr.strip() or out.stdout.strip()}")
    if not want_json:
        return out.stdout
    data = json.loads(out.stdout)
    return data.get("structuredContent", data)


def wake(seed, text):
    res = volty("debug", "wake-sync", f"--from={seed}", f"--text={text}")
    tries = 0
    while res.get("pending") and tries < 12:
        time.sleep(5)
        tries += 1
        res = volty("debug", "wake-status", f"--conversation-id={res['conversationId']}")
    return res


def run(scn, run_tag):
    seed = f"{scn['id'].lower()}-{run_tag}"
    cost = 0
    conv = None
    for text in scn["turns"]:
        res = wake(seed, text)
        conv = res.get("conversationId", conv)
        cost += res.get("costMicros") or 0
    time.sleep(2)
    msgs = volty("messaging", "list-messages", f"--conversation-id={conv}")["messages"]
    trace = volty("debug", "trace", f"--conversation-id={conv}")["items"]
    info = volty("conversations", "get", f"--conversation-id={conv}")
    contact = volty("contacts", "get", f"--id=cnt:{info['contactId']}")
    contact = contact.get("contact", contact)
    ops = [i["op"] for i in trace if i.get("kind") == "operation" and i.get("sessionId")]
    replies = [m["text"] for m in msgs if m["role"] == "agent" and m["visibility"] == "public"]
    # After a hand-off Volty steps back: its next answer is a draft for the strategist, which counts.
    drafts = sum(1 for o in ops if o == "messaging draft")
    attrs = contact.get("attributes") or {}
    labels = contact.get("segments") or contact.get("labels") or []

    exp = scn["expect"]
    checks = []
    if exp.get("tier"):
        checks.append((f"tier = {exp['tier']}", attrs.get("lead_tier") == exp["tier"], f"got {attrs.get('lead_tier')!r}"))
    handed = any(o.startswith(HANDOFF_OPS) for o in ops)
    if exp.get("handoff") is not None:
        checks.append((f"handed off = {exp['handoff']}", handed == exp["handoff"], f"got {handed}"))
    joined = "\n".join(replies)
    for pat in exp.get("must", []):
        checks.append((f"reply contains /{pat}/", bool(re.search(pat, joined, re.I)), ""))
    for pat in exp.get("must_not", []):
        hit = re.search(pat, joined, re.I)
        checks.append((f"reply avoids /{pat}/", not hit, f"found {hit.group(0)!r}" if hit else ""))
    checks.append(("answered every turn (reply, or draft after hand-off)",
                   len(replies) + drafts >= len(scn["turns"]), f"{len(replies)} replies, {drafts} drafts"))
    checks.append(("hands off at most once (no assign then un-assign)", ops.count("conversations assign-team") <= 1,
                   f"{ops.count('conversations assign-team')} assign-team calls"))
    checks.append(("never tells the lead its tier", not re.search(r"(hot|qualified) lead|tier [ABCD]\b", joined, re.I), ""))
    passed = all(ok for _, ok, _ in checks)
    return {
        "scn": scn, "conv": conv, "passed": passed, "checks": checks, "handed": handed,
        "cost": cost / 1e6, "attrs": attrs, "labels": labels, "ops": ops, "msgs": msgs,
    }


def report(results, run_tag):
    lines = [f"# Lead qualifier test run {run_tag}", ""]
    n = sum(r["passed"] for r in results)
    lines += [f"{n} of {len(results)} scenarios passed. Cost ${sum(r['cost'] for r in results):.4f}.", ""]
    lines += ["| Id | Scenario | Result | Tier set | Handed off | Cost |", "| --- | --- | --- | --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r['scn']['id']} | {r['scn']['name']} | {'PASS' if r['passed'] else 'FAIL'} | "
                     f"{r['attrs'].get('lead_tier', '-')} | {'yes' if r['handed'] else 'no'} | ${r['cost']:.4f} |")
    for r in results:
        lines += ["", f"## {r['scn']['id']} {r['scn']['name']} ({'PASS' if r['passed'] else 'FAIL'})",
                  f"Conversation `{r['conv']}`", ""]
        for name, ok, note in r["checks"]:
            lines.append(f"- [{'x' if ok else ' '}] {name}{' (' + note + ')' if note and not ok else ''}")
        lines += ["", "**Transcript**", ""]
        for m in r["msgs"]:
            if m["visibility"] != "public":
                continue
            who = "Lead" if m["role"] == "contact" else "Agent"
            lines.append(f"> **{who}:** " + m["text"].replace("\n", "\n> "))
            lines.append(">")
        lines += ["", f"**Contact fields:** `{json.dumps(r['attrs'], ensure_ascii=False)}`",
                  f"**Labels:** {r['labels']}", f"**Agent ops:** {', '.join(r['ops'])}"]
    return "\n".join(lines) + "\n"


def main():
    scenarios = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    wanted = set(sys.argv[1:])
    if wanted:
        scenarios = [s for s in scenarios if s["id"] in wanted]
    run_tag = datetime.now(timezone.utc).strftime("%m%d%H%M")
    results = []
    for s in scenarios:
        print(f"{s['id']} {s['name']} ...", flush=True)
        try:
            r = run(s, run_tag)
        except Exception as e:  # keep going: one broken scenario should not hide the others
            print(f"  ERROR {e}", flush=True)
            continue
        print(f"  {'PASS' if r['passed'] else 'FAIL'}  tier={r['attrs'].get('lead_tier')} handoff={r['handed']}", flush=True)
        results.append(r)
    out = HERE / "results" / f"run-{run_tag}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report(results, run_tag), encoding="utf-8")
    print(f"\n{sum(r['passed'] for r in results)}/{len(results)} passed. Report: {out}")


if __name__ == "__main__":
    main()
