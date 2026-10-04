#!/usr/bin/env python3
"""
NASH-02 Stage to GitHub Release Tool
Uploads rendered local video master assets to GitHub Releases as a staging storage
for automated scheduling by GitHub Actions.
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path

REPO_DIR = Path("C:/Users/K4G3/Documents/Github/nashtaktik")
PROD_BASE = Path("C:/Users/K4G3/social-fleet-assets/nash/NASH-02_nash_taktik_sejarah/production")
REPO_NAME = "nashqroulm-rgb/nashtaktik"

def get_gh_env():
    """Retrieve GitHub credentials from Git Credential Manager."""
    env = os.environ.copy()
    if "GH_TOKEN" in env or "GITHUB_TOKEN" in env:
        return env
        
    try:
        p = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        out, _ = p.communicate("protocol=https\nhost=github.com\n\n")
        for line in out.splitlines():
            if line.startswith("password="):
                token = line.split("=", 1)[1].strip()
                env["GH_TOKEN"] = token
                break
    except Exception as e:
        print(f"[Warning] Failed to fetch token from git credential manager: {e}")
        
    return env

def stage_week_long_form(week_str: str):
    env = get_gh_env()
    week_num = int(week_str.replace("week_", "").replace("week", ""))
    
    prod_dir = PROD_BASE / f"week_{week_num:03d}"
    out_dir = prod_dir / "output"
    
    if not out_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {out_dir}")
        
    # Find master mp4
    mp4_files = list(out_dir.glob("*Master*.mp4")) or list(out_dir.glob("*.mp4"))
    if not mp4_files:
        raise FileNotFoundError(f"No master MP4 found in {out_dir}")
    video_path = mp4_files[0]
    
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"\n[Stage] Found Master Video: {video_path.name} ({file_size_mb:.2f} MB)")
    
    # Release Tag
    tag_name = f"v-week-{week_num:03d}-long"
    release_title = f"NASH-02 Week {week_num:03d}: Long-Form Master Staging"
    release_notes = (
        f"Automated Staging Asset for NASH-02 Week {week_num:03d}.\n"
        f"File: {video_path.name} ({file_size_mb:.2f} MB)\n"
        f"This asset will be downloaded by GitHub Actions for scheduled publishing, "
        f"then automatically pruned once verified."
    )
    
    # 1. Check if release already exists
    check_cmd = ["gh", "release", "view", tag_name, "--repo", REPO_NAME]
    res_check = subprocess.run(check_cmd, env=env, capture_output=True, text=True)
    
    if res_check.returncode != 0:
        print(f"[Stage] Creating new release tag: {tag_name}...")
        create_cmd = [
            "gh", "release", "create", tag_name,
            str(video_path),
            "--title", release_title,
            "--notes", release_notes,
            "--repo", REPO_NAME
        ]
        t0 = time.time()
        res_create = subprocess.run(create_cmd, env=env, capture_output=True, text=True)
        dt = time.time() - t0
        if res_create.returncode != 0:
            raise RuntimeError(f"Failed to create release: {res_create.stderr}")
        print(f"[Stage] Release created and video uploaded successfully in {dt:.1f}s!")
    else:
        print(f"[Stage] Release {tag_name} already exists. Uploading/clobbering asset...")
        upload_cmd = [
            "gh", "release", "upload", tag_name,
            str(video_path),
            "--clobber",
            "--repo", REPO_NAME
        ]
        t0 = time.time()
        res_upload = subprocess.run(upload_cmd, env=env, capture_output=True, text=True)
        dt = time.time() - t0
        if res_upload.returncode != 0:
            raise RuntimeError(f"Failed to upload asset: {res_upload.stderr}")
        print(f"[Stage] Asset uploaded successfully in {dt:.1f}s!")
        
    # 2. Update long_form.json in curriculum
    curr_json = REPO_DIR / "curriculum" / f"week_{week_num:03d}" / "long_form.json"
    if curr_json.exists():
        with open(curr_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        data["staging"] = {
            "storage": "github_release",
            "release_tag": tag_name,
            "asset_name": video_path.name,
            "size_mb": round(file_size_mb, 2),
            "staged_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["status"] = "STAGED_IN_RELEASE"
        
        with open(curr_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[Stage] Updated {curr_json.name} with staging metadata.")
        
    # 3. Update state/campaign_state.json
    state_json = REPO_DIR / "state" / "campaign_state.json"
    if state_json.exists():
        with open(state_json, "r", encoding="utf-8") as f:
            state = json.load(f)
            
        stg_key = f"week_{week_num:03d}_staging"
        if stg_key in state:
            state[stg_key]["long_form"]["release_tag"] = tag_name
            state[stg_key]["long_form"]["asset_name"] = video_path.name
            state[stg_key]["long_form"]["status"] = "STAGED_IN_RELEASE"
            
        with open(state_json, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"[Stage] Updated campaign_state.json.")

    print("\n" + "=" * 60)
    print(f"  WEEK {week_num:03d} LONG-FORM STAGED SUCCESSFULLY IN GITHUB RELEASES!")
    print(f"  Tag   : {tag_name}")
    print(f"  Asset : {video_path.name}")
    print(f"  Size  : {file_size_mb:.2f} MB")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Stage rendered master video to GitHub Releases")
    parser.add_argument("--week", default="week_004", help="Week directory, e.g. week_004")
    args = parser.parse_args()
    
    stage_week_long_form(args.week)

if __name__ == "__main__":
    main()
