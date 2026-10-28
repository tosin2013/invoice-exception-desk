#!/usr/bin/env python3
"""Warning-only drift check between ROADMAP.md and specs/NNN-*/ (PLAYBOOK: "PM: plan the roadmap first").

Checks:
  1. every specs/NNN-* dir is referenced by a ROADMAP row (or listed under "Specs outside this roadmap");
  2. every row at specified, building or done names a spec dir that exists;
  3. every done row has a PR link ("PR #N" or a .../pull/N URL).
Also warns on a status outside planned|specified|building|done|dropped.

A spec dir can be branch-qualified, "l5-setup:specs/003-desk-import/", for repos whose specs live on a
different branch from the roadmap. Those are read with `git ls-tree` from origin/<branch> (or a local
<branch>). Unqualified "specs/NNN-x/" means the checked-out tree. Standard library only. It prints
GitHub `::warning::` annotations and ALWAYS exits 0; it never fails a build.
"""
import os
import re
import subprocess
import sys

STATUSES = {"planned", "specified", "building", "done", "dropped"}
NEEDS_SPEC = {"specified", "building", "done"}
QUALIFIED = re.compile(r"([A-Za-z0-9._/-]+?):(specs/\d{3}-[A-Za-z0-9._-]+)")
BARE = re.compile(r"(?<![\w/:.-])(specs/\d{3}-[A-Za-z0-9._-]+)")
PR_LINK = re.compile(r"\bPR #\d+|/pull/\d+")
SPEC_DIR_NAME = re.compile(r"^\d{3}-")


FILE = "ROADMAP.md"


def warn(msg, line=None):
    loc = f" file={FILE},line={line}" if line else f" file={FILE}"
    print(f"::warning{loc}::{msg}")


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def resolve_ref(branch):
    for ref in (f"origin/{branch}", branch):
        if git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"):
            return ref
    return None


def spec_dirs_on(branch):
    """Set of 'specs/NNN-x' dirs on a branch, or None if the branch can't be read."""
    if branch is None:
        if not os.path.isdir("specs"):
            return set()
        return {f"specs/{d}" for d in os.listdir("specs")
                if SPEC_DIR_NAME.match(d) and os.path.isdir(os.path.join("specs", d))}
    ref = resolve_ref(branch)
    if ref is None:
        return None
    out = git("ls-tree", "-d", "--name-only", f"{ref}:specs")
    if out is None:
        return set()
    return {f"specs/{d}" for d in out.split() if SPEC_DIR_NAME.match(d)}


def refs_in(text):
    """[(branch or None, 'specs/NNN-x')] referenced in text."""
    found = [(b, d) for b, d in QUALIFIED.findall(text)]
    found += [(None, d) for d in BARE.findall(QUALIFIED.sub("", text))]
    return found


def main(path="ROADMAP.md"):
    global FILE
    FILE = path
    if not os.path.exists(path):
        warn(f"{path} not found; nothing to check")
        return
    lines = open(path, encoding="utf-8").read().splitlines()
    header = None
    rows = []
    accounted = set()
    outside = False
    for n, line in enumerate(lines, 1):
        if line.startswith("#"):
            outside = "specs outside this roadmap" in line.lower()
        if outside:
            accounted.update(refs_in(line))
        if not line.startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if "id" in header and "status" in header and "spec dir" in header:
            rows.append((n, dict(zip(header, cells))))

    if not rows:
        warn("no roadmap table with ID, Status and Spec dir columns found")
        return

    branches = {None}
    for _, row in rows:
        branches.update(b for b, _ in refs_in(row.get("spec dir", "")))
    branches.update(b for b, _ in accounted)
    existing = {b: spec_dirs_on(b) for b in branches}

    for n, row in rows:
        rid, status = row.get("id", "?"), row.get("status", "").strip("` ").lower()
        if status not in STATUSES:
            warn(f"{rid}: status '{status}' is not one of {'|'.join(sorted(STATUSES))}", n)
        dirs = refs_in(row.get("spec dir", ""))
        accounted.update(dirs)
        if status in NEEDS_SPEC:
            if not dirs:
                warn(f"{rid} is '{status}' but names no spec dir", n)
            for b, d in dirs:
                have = existing.get(b)
                where = f"branch {b}" if b else "this checkout"
                if have is None:
                    warn(f"{rid}: can't read branch '{b}' to check {d} (fetch it, e.g. fetch-depth: 0)", n)
                elif d not in have:
                    warn(f"{rid}: spec dir {d} does not exist on {where}", n)
        if status == "done" and not PR_LINK.search(row.get("issue / pr", "")):
            warn(f"{rid} is 'done' but has no PR link in Issue / PR", n)

    for b, have in existing.items():
        for d in sorted(have or ()):
            if (b, d) not in accounted:
                where = f"{b}:{d}" if b else d
                warn(f"{where} has no ROADMAP row (add one, or list it under 'Specs outside this roadmap')")

    checked = ", ".join(sorted(b or "this checkout" for b in existing))
    print(f"roadmap drift check: {len(rows)} rows; spec dirs read from: {checked}")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:2])
    except Exception as exc:  # warning-only: never fail the build
        print(f"::warning::roadmap drift check could not run: {exc}")
    sys.exit(0)
