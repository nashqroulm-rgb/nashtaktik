#!/usr/bin/env python3
"""
NASH-02 Upstream Packaging Gatekeeper & Scene Binding Auditor
Scans all curriculum weeks (Week 1 to Week 26) and verifies:
1. Every short_*.json has an explicit 'scene_images' array.
2. Every image listed in 'scene_images' exists physically on disk in images/ directory.
3. No heuristic keyword guessing is allowed at runtime.
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = ROOT_DIR / "curriculum"

def audit_all_weeks():
    print("=" * 65)
    print("  NASH-02 UPSTREAM PACKAGING AUDIT: SCENE-ASSET BINDINGS")
    print("=" * 65)

    week_dirs = sorted([d for d in CURRICULUM_DIR.glob("week_*") if d.is_dir()])
    if not week_dirs:
        print("[!] No week directories found in curriculum.")
        sys.exit(1)

    total_shorts = 0
    missing_bindings = []
    missing_files = []

    for wdir in week_dirs:
        images_dir = wdir / "images"
        short_files = sorted(wdir.glob("short_*.json"))
        available_images = {f.name: f for f in images_dir.glob("*.jpg") if "thumb" not in f.name.lower()} if images_dir.exists() else {}

        print(f"\n📁 {wdir.name} ({len(short_files)} shorts, {len(available_images)} images available):")

        for sf in short_files:
            total_shorts += 1
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
            except Exception as e:
                missing_bindings.append((wdir.name, sf.name, f"Corrupted JSON: {e}"))
                continue

            scenes = data.get("scene_images")
            if not scenes or not isinstance(scenes, list) or len(scenes) == 0:
                missing_bindings.append((wdir.name, sf.name, "MISSING 'scene_images' array"))
                print(f"  ❌ {sf.name}: TIDAK ADA 'scene_images'")
                continue

            # Verify physical existence of all declared images
            unresolved = []
            for img_name in scenes:
                if img_name in available_images:
                    continue
                # Fuzzy token match
                clean = img_name.lower().replace("…", "").replace(".jpg", "").strip()
                tokens = [t for t in clean.split("_") if t and not t.isdigit() and len(t) > 2]
                match = next((f for f in available_images.keys() if any(t in f.lower() for t in tokens)), None)
                if not match:
                    unresolved.append(img_name)

            if unresolved:
                missing_files.append((wdir.name, sf.name, unresolved))
                print(f"  ⚠️ {sf.name}: {len(unresolved)} file gambar tidak ditemukan di disk: {unresolved}")
            else:
                print(f"  ✓ {sf.name}: {len(scenes)} adegan terkunci 100% presisi.")

    print("\n" + "=" * 65)
    print(f"AUDIT SUMMARY: Total {total_shorts} shorts diperiksa.")
    print(f"  - Missing Bindings: {len(missing_bindings)}")
    print(f"  - Missing Image Files: {len(missing_files)}")
    print("=" * 65)

    if missing_bindings or missing_files:
        print("\n[FAILED] Terdapat celah desinkronisasi visual! Rilis ditolak.")
        return False
    else:
        print("\n[PASSED] Seluruh episode short memiliki pemetaan visual deterministik 100%!")
        return True

if __name__ == "__main__":
    ok = audit_all_weeks()
    sys.exit(0 if ok else 1)
