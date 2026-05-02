#!/usr/bin/env python3
"""Download 50 clothing test images for ATTREQ wardrobe testing."""

import os
import time

import requests

OUTDIR = os.path.join(os.path.dirname(__file__), "test_images")

IMAGES = [
    # Tops
    ("1620799140408-edc6dcb6d633", "t01_white_tshirt.jpg"),
    ("1556821840-3a63f95609a7", "t02_black_tshirt.jpg"),
    ("1581655353564-df123a1eb820", "t03_navy_tshirt.jpg"),
    ("1503341504253-dff4815485f1", "t04_vintage_tshirt.jpg"),
    ("1571019613454-1cb2f99b2d8b", "t05_polo_shirt.jpg"),
    ("1603252109303-2751441dd157", "t06_white_dress_shirt.jpg"),
    ("1596755094514-f87e34085b2c", "t07_plaid_flannel_shirt.jpg"),
    ("1598030474564-d9a45c780e9a", "t08_casual_button_shirt.jpg"),
    # Sweaters / Knitwear
    ("1551028719-00167b16eac5", "s01_grey_cardigan.jpg"),
    ("1576671081524-7d4f30aed5f1", "s02_burgundy_sweater.jpg"),
    ("1467043237213-65f3bfa2741a", "s03_knit_sweater.jpg"),
    ("1606107557195-0e29a4b5b4aa", "s04_green_sweater.jpg"),
    ("1620799139834-ee7bedb72c44", "s05_beige_sweater.jpg"),
    ("1583744948174-20a2c897a39f", "s06_turtleneck_sweater.jpg"),
    # Hoodies
    ("1595777457583-95e059d581b8", "h01_red_hoodie.jpg"),
    ("1629136234-eabd16a62a74", "h02_oversized_hoodie.jpg"),
    # Jackets / Outerwear
    ("1591047139829-d91aecb6caea", "j01_black_leather_jacket.jpg"),
    ("1578932750294-f5075e85f44a", "j02_denim_jacket.jpg"),
    ("1523381294911-8d3cead13475", "j03_black_blazer.jpg"),
    ("1544923246-a9b2a560bb1b", "j04_trench_coat.jpg"),
    ("1548624149-f2ae70b39d28", "j05_puffer_jacket.jpg"),
    ("1518459428-b8b5da56e1c8", "j06_olive_military_jacket.jpg"),
    ("1548027033-0d73b30cb2af", "j07_camel_wool_coat.jpg"),
    ("1520975954148-c51e84e7cac3", "j08_winter_coat.jpg"),
    # Pants / Jeans
    ("1542272604-787c3835535d", "p01_blue_jeans.jpg"),
    ("1473966968600-fa4f9e6e8bd9", "p02_black_skinny_jeans.jpg"),
    ("1562516710-3e5acb6f8d0e", "p03_dark_wash_jeans.jpg"),
    ("1624378439575-d8705ad7ae80", "p04_khaki_pants.jpg"),
    ("1511463054-e12d7b231e02", "p05_white_trousers.jpg"),
    ("1617952986-90398b8bffce", "p06_white_chinos.jpg"),
    ("1565974767521-40ee0d49a3d4", "p07_khaki_shorts.jpg"),
    ("1538805083-d1ab52d9f9c6", "p08_running_shorts.jpg"),
    # Dresses / Skirts
    ("1614676471928-2ed0ad1061a4", "d01_black_dress.jpg"),
    ("1539533018447-63fcce2678e3", "d02_floral_summer_dress.jpg"),
    ("1583496661135-56bdb16eacac", "d03_yellow_summer_dress.jpg"),
    ("1572804013-4673cc2ec3c7", "d04_midi_dress.jpg"),
    ("1612337823-3e5d5d79bf02", "d05_red_dress.jpg"),
    ("1526779259212-3e3b1c6bbfae", "d06_bodycon_dress.jpg"),
    ("1515886657613-9f3515b0c78f", "d07_floral_midi_skirt.jpg"),
    ("1499971855286-b0c3de2adeba", "d08_evening_gown.jpg"),
    # Formal / Suits
    ("1507679799987-c73779587ccf", "f01_business_suit.jpg"),
    # Activewear
    ("1517836357463-d25dfeac3438", "a01_workout_leggings.jpg"),
    ("1556804335-2fafc88cd5a0", "a02_sports_jersey.jpg"),
    # Footwear
    ("1541099649105-f69ad21f3246", "fw01_white_sneakers.jpg"),
    ("1600185365483-26d3aa097614", "fw02_running_shoes.jpg"),
    ("1543163521-1bf8a9b6db41", "fw03_brown_leather_boots.jpg"),
    ("1460353581641-37baddab0fa2", "fw04_ankle_boots.jpg"),
    ("1588361861-dd744a37d2af", "fw05_black_oxford_shoes.jpg"),
    ("1525966222134-84e702c8a7e5", "fw06_loafers.jpg"),
    # Accessories
    ("1553062407-98eeb64c6a62", "ac01_beanie.jpg"),
    ("1553482418-7d5b4cfe6456", "ac02_striped_scarf.jpg"),
    ("1611558709015-09abb8bcc6b8", "ac03_baseball_cap.jpg"),
    ("1614082800568-5e3ca3d53b34", "ac04_leather_belt.jpg"),
    ("1564438268-d01b5b08e2ab", "ac05_aviator_sunglasses.jpg"),
    ("1591291083839-4e4d70ad10a8", "ac06_luxury_watch.jpg"),
    ("1512436991641-6933ad6b5d93", "ac07_wrap_kimono.jpg"),
]

BASE = "https://images.unsplash.com/photo-{}?w=800&auto=format&fit=crop"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def download(photo_id: str, filename: str) -> bool:
    filepath = os.path.join(OUTDIR, filename)
    if os.path.exists(filepath):
        print(f"skip  {filename} (exists)")
        return True
    url = BASE.format(photo_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        os.makedirs(OUTDIR, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(r.content)
        print(f"ok    {filename} ({len(r.content):,} bytes)")
        return True
    except Exception as e:
        print(f"fail  {filename}: {e}")
        return False


def main():
    print(f"Target: {OUTDIR}")
    print(f"Images in list: {len(IMAGES)}")
    print()
    ok = sum(download(pid, fn) or time.sleep(0.3) or False for pid, fn in IMAGES)
    total = len(list(os.scandir(OUTDIR)))
    print(f"\nDone: {ok}/{len(IMAGES)} downloaded | {total} total in folder")


if __name__ == "__main__":
    main()
