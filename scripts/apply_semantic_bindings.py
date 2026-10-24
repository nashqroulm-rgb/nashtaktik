#!/usr/bin/env python3
"""
Semantic Scene Image Binder for NASH-02 (Weeks 4, 5, 6)
Maps each sentence in each short to a visually and semantically coherent image.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = ROOT_DIR / "curriculum"

WEEK_005_MAPPING = {
    "short_01_senin.json": [
        "Roman_Consul_viewing_legionaries…_20261004210851.jpg",
        "Roman_legionary_ranks_marching_road_20261004210851.jpg",
        "Scout_viewing_Lake_Trasimene_defile_20261004210852.jpg",
        "Roman_legionaries_marching_in_mist_20261004210846.jpg",
        "Bronze_helmet_in_lake_mud_20261004210851.jpg"
    ],
    "short_02_selasa.json": [
        "Sun_rising_over_Lake_Trasimene_20261004210845.jpg",
        "Roman_legionaries_marching_in_mist_20261004210846.jpg",
        "Slingers_preparing_ambush_on_mou…_20261004210849.jpg",
        "Warrior_blowing_bronze_war_trumpet_20261004210846.jpg",
        "Warriors_charging_down_grassy_slope_20261004210842.jpg"
    ],
    "short_03_rabu.json": [
        "Roman_legionaries_retreating_at_…_20261004210851.jpg",
        "Scout_viewing_Lake_Trasimene_defile_20261004210852.jpg",
        "Roman_legionaries_retreating_at_…_20261004210851.jpg",
        "Chieftain_galloping_toward_Roman…_20261004210843.jpg",
        "Lake_Trasimene_shoreline_after_b…_20261004210844.jpg"
    ],
    "short_04_kamis.json": [
        "Veteran_striking_Roman_shield_20261004210842.jpg",
        "Slingers_preparing_ambush_on_mou…_20261004210849.jpg",
        "Iberian_infantrymen_standing_in_…_20261004210843.jpg",
        "Veteran_striking_Roman_shield_20261004210842.jpg",
        "Warriors_advancing_through_Tusca…_20261004210851.jpg"
    ],
    "short_05_jumat.json": [
        "General_Hannibal_overlooking_Etr…_20261004210851.jpg",
        "Raiders_burning_Etruscan_wheat_g…_20261004210851.jpg",
        "Roman_Consul_viewing_legionaries…_20261004210851.jpg",
        "Roman_legionary_ranks_marching_road_20261004210851.jpg",
        "Hannibal_convening_war_council_20261004210850.jpg"
    ],
    "short_06_sabtu.json": [
        "General_Hannibal_overlooking_Etr…_20261004210851.jpg",
        "Hannibal_convening_war_council_20261004210850.jpg",
        "Sun_rising_over_Lake_Trasimene_20261004210845.jpg",
        "Warriors_advancing_through_Tusca…_20261004210851.jpg",
        "Lake_Trasimene_shoreline_after_b…_20261004210844.jpg"
    ]
}

WEEK_006_MAPPING = {
    "short_01_senin.json": [
        "Roman_commanders_viewing_army_camp_20261013210601.jpg",
        "Roman_army_marching_on_road_20261013210601.jpg",
        "Roman_legionary_ranks_advancing_20261013210601.jpg",
        "Roman_legionaries_surging_forward_20261013210601.jpg",
        "Battle_lines_of_Cannae_20261013210601.jpg",
        "Commanders_standing_before_advan…_20261013210601.jpg"
    ],
    "short_02_selasa.json": [
        "General_Hannibal_overseeing_capt…_20261013210601.jpg",
        "Battle_lines_of_Cannae_20261013210601.jpg",
        "Celtic_and_Iberian_infantry_stan…_20261013210601.jpg",
        "Warriors_executing_backward_figh…_20261013210601.jpg",
        "Libyan_heavy_infantry_standing_s…_20261013210601.jpg",
        "Infantry_attacking_Roman_flanks_20261013210601.jpg"
    ],
    "short_03_rabu.json": [
        "Battle_lines_of_Cannae_20261013210601.jpg",
        "Roman_soldiers_clashing_with_shi…_20261013210601.jpg",
        "Infantry_attacking_Roman_flanks_20261013210601.jpg",
        "Wounded_consul_sitting_on_battle…_20261013211149.jpg",
        "Roman_citizens_gazing_at_couriers_20261013210601.jpg",
        "Senators_viewing_Roman_Forum_20261013211210.jpg"
    ],
    "short_04_kamis.json": [
        "Cavalry_galloping_along_riverbank_20261013210601.jpg",
        "Cavalry_charging_Roman_army_20261013210601.jpg",
        "Roman_cavalrymen_lining_river_banks_20261013210601.jpg",
        "Cavalrymen_galloping_in_circles_20261013210601.jpg",
        "Battle_lines_of_Cannae_20261013210601.jpg"
    ],
    "short_05_jumat.json": [
        "Battle_lines_of_Cannae_20261013210601.jpg",
        "Roman_legionaries_raising_shield…_20261013210601.jpg",
        "Warriors_executing_backward_figh…_20261013210601.jpg",
        "Roman_legionaries_surging_forward_20261013210601.jpg",
        "Carthaginian_sentries_standing_o…_20261013210601.jpg"
    ],
    "short_06_sabtu.json": [
        "General_Hannibal_overseeing_capt…_20261013210601.jpg",
        "Battle_lines_of_Cannae_20261013210601.jpg",
        "Celtic_and_Iberian_infantry_stan…_20261013210601.jpg",
        "Infantry_attacking_Roman_flanks_20261013210601.jpg",
        "Commanders_standing_before_advan…_20261013210601.jpg"
    ]
}

def apply_mapping():
    print("Applying Semantic Visual Bindings for Week 5...")
    w5_dir = CURRICULUM_DIR / "week_005"
    for fname, imgs in WEEK_005_MAPPING.items():
        fpath = w5_dir / fname
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        data["scene_images"] = imgs
        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ {fname} -> {len(imgs)} semantic scenes bound.")

    print("\nApplying Semantic Visual Bindings for Week 6...")
    w6_dir = CURRICULUM_DIR / "week_006"
    for fname, imgs in WEEK_006_MAPPING.items():
        fpath = w6_dir / fname
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        data["scene_images"] = imgs
        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ {fname} -> {len(imgs)} semantic scenes bound.")

if __name__ == "__main__":
    apply_mapping()
