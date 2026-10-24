#!/usr/bin/env python3
"""Validate MyTESY HACS package metadata."""
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def check(root=ROOT):
    errors=[]
    required=["README.md","LICENSE.txt","hacs.json",".github/workflows/validate.yml",
        "custom_components/tesy/__init__.py","custom_components/tesy/manifest.json",
        "custom_components/tesy/strings.json","custom_components/tesy/translations/en.json",
        "custom_components/tesy/brand/icon.png",
        "docs/licenta-originala-ro.md"]
    for p in required:
        if not (root/p).is_file():
            errors.append("Missing: "+p)
    component=root/"custom_components"
    if component.is_dir() and sorted(x.name for x in component.iterdir() if x.is_dir()) != ["tesy"]:
        errors.append("Expected only custom_components/tesy")
    f=root/"custom_components/tesy/manifest.json"
    if f.is_file():
        m=json.loads(f.read_text())
        if m.get("domain")!="tesy" or m.get("version")!="1.1.2":
            errors.append("Manifest domain/version invalid")
        if not m.get("codeowners") or not m.get("documentation") or not m.get("issue_tracker"):
            errors.append("Missing codeowner/docs/issues")
        if list(m) != ["domain","name"]+sorted(k for k in m if k not in ["domain","name"]):
            errors.append("Manifest key order invalid")
        if not re.fullmatch(r"\d+\.\d+\.\d+",str(m.get("version",""))):
            errors.append("Invalid version")
    source=root/"custom_components/tesy/strings.json"
    fallback=root/"custom_components/tesy/translations/en.json"
    if source.is_file() and fallback.is_file():
        try:
            if json.loads(source.read_text(encoding="utf-8")) != json.loads(fallback.read_text(encoding="utf-8")):
                errors.append("English fallback en.json must match strings.json")
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append(f"Invalid translation JSON: {exc}")
    return errors
if __name__=="__main__":
    problems=check()
    for p in problems: print(p,file=sys.stderr)
    if problems: raise SystemExit(1)
    print("PASS MyTESY HACS layout")
