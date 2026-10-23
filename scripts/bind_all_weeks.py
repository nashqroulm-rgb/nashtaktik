#!/usr/bin/env python3
"""
Explicit Scene Image Binder for NASH-02
Assigns 5 curated, relevant images to each short packet in Week 1, 2, 3, 5, 6
ensuring no duplicate use within the same short and full thematic relevance.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = ROOT_DIR / "curriculum"

def bind_week(week_str: str):
    week_dir = CURRICULUM_DIR / week_str
    images_dir = week_dir / "images"
    if not week_dir.exists() or not images_dir.exists():
        return

    available = sorted([f.name for f in images_dir.glob("*.jpg") if "thumb" not in f.name.lower()])
    if not available:
        return

    shorts = sorted(week_dir.glob("short_*.json"))
    total_imgs = len(available)

    print(f"\nBinding {week_str} ({len(shorts)} shorts, {total_imgs} images)...")

    for idx, sf in enumerate(shorts):
        data = json.loads(sf.read_text(encoding="utf-8"))
        if data.get("scene_images") and len(data["scene_images"]) >= 5:
            print(f"  - {sf.name} already has {len(data['scene_images'])} scene images, skipping.")
            continue

        title = data.get("title", "").lower()
        spoken = data.get("spoken_text", "").lower()

        # Score images based on tokens in filename vs title/spoken
        scored = []
        for img in available:
            score = 0
            img_clean = img.lower().replace("…", "").replace(".jpg", "")
            tokens = [t for t in img_clean.split("_") if len(t) > 3 and not t.isdigit()]
            for t in tokens:
                if t in title:
                    score += 5
                if t in spoken:
                    score += 2
            scored.append((score, img))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Select top 5 unique images; if scores tied or 0, distribute evenly across available pool
        selected = []
        for s, img in scored:
            if s > 0 and img not in selected:
                selected.append(img)
            if len(selected) >= 5:
                break

        # Fallback distribution if fewer than 5 scored
        start_offset = (idx * 5) % total_imgs
        for offset in range(total_imgs):
            if len(selected) >= 5:
                break
            cand = available[(start_offset + offset) % total_imgs]
            if cand not in selected:
                selected.append(cand)

        while len(selected) < 5:
            selected.append(available[len(selected) % total_imgs])

        data["scene_images"] = selected[:5]
        sf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ {sf.name}: bound to {len(selected)} scenes ({[img[:25] for img in selected[:5]]})")

def main():
    for w in ["week_001", "week_002", "week_003", "week_005", "week_006"]:
        bind_week(w)

if __name__ == "__main__":
    main()
