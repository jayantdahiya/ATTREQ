#!/usr/bin/env python3
"""
Script to download real test clothing images for ATTREQ wardrobe API testing.
Uses actual clothing images from free stock photo sites.
"""

import os
import time

import requests


def download_image(url: str, filename: str, directory: str = "test_images"):
    """Download an image from URL and save it locally."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Set headers to mimic browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # Download image
        print(f"⏳ Downloading: {filename}...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save image
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
        return filepath

    except Exception as e:
        print(f"❌ Failed to download {filename}: {str(e)}")
        return None

def main():
    """Download sample clothing images for testing."""

    # Real clothing images from Unsplash with specific IDs
    # These are actual direct image URLs that will work
    test_images = [
        {
            "url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=800&auto=format&fit=crop",
            "filename": "01_white_tshirt.jpg",
            "description": "White T-shirt"
        },
        {
            "url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=800&auto=format&fit=crop",
            "filename": "02_blue_jeans.jpg",
            "description": "Blue Jeans"
        },
        {
            "url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&auto=format&fit=crop",
            "filename": "03_black_leather_jacket.jpg",
            "description": "Black Leather Jacket"
        },
        {
            "url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop",
            "filename": "04_red_hoodie.jpg",
            "description": "Red Hoodie"
        },
        {
            "url": "https://images.unsplash.com/photo-1614676471928-2ed0ad1061a4?w=800&auto=format&fit=crop",
            "filename": "05_black_dress.jpg",
            "description": "Black Dress"
        },
        {
            "url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop",
            "filename": "06_striped_sweater.jpg",
            "description": "Striped Sweater"
        },
        {
            "url": "https://images.unsplash.com/photo-1578932750294-f5075e85f44a?w=800&auto=format&fit=crop",
            "filename": "07_denim_jacket.jpg",
            "description": "Denim Jacket"
        },
        {
            "url": "https://images.unsplash.com/photo-1603252109303-2751441dd157?w=800&auto=format&fit=crop",
            "filename": "08_white_dress_shirt.jpg",
            "description": "White Dress Shirt"
        },
        {
            "url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800&auto=format&fit=crop",
            "filename": "09_khaki_pants.jpg",
            "description": "Khaki Pants"
        },
        {
            "url": "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=800&auto=format&fit=crop",
            "filename": "10_floral_summer_dress.jpg",
            "description": "Floral Summer Dress"
        },
        {
            "url": "https://images.unsplash.com/photo-1523381294911-8d3cead13475?w=800&auto=format&fit=crop",
            "filename": "11_black_blazer.jpg",
            "description": "Black Blazer"
        },
        {
            "url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&auto=format&fit=crop",
            "filename": "12_grey_cardigan.jpg",
            "description": "Grey Cardigan"
        }
    ]

    print("=" * 60)
    print("🔄 DOWNLOADING TEST CLOTHING IMAGES FOR ATTREQ")
    print("=" * 60)
    print()

    downloaded_files = []

    for img in test_images:
        filepath = download_image(img["url"], img["filename"])
        if filepath:
            downloaded_files.append({
                "filepath": filepath,
                "description": img["description"],
                "filename": img["filename"]
            })
        # Small delay to be respectful to the server
        time.sleep(0.5)

    print()
    print("=" * 60)
    print(f"✅ Successfully downloaded {len(downloaded_files)}/{len(test_images)} images")
    print("=" * 60)
    print()
    print("📁 Files saved to: test_images/")
    print()
    print("📋 Downloaded items:")
    for item in downloaded_files:
        print(f"   - {item['filename']}: {item['description']}")

    print()
    print("=" * 60)
    print("🧪 TESTING YOUR WARDROBE API")
    print("=" * 60)
    print()
    print("Step 1: Register/Login to get JWT token")
    print("curl -X POST 'http://localhost:8000/api/v1/auth/register' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"email\": \"test@example.com\", \"password\": \"Test123!\", \"full_name\": \"Test User\"}'")
    print()
    print("Step 2: Upload an item to your wardrobe")
    print("curl -X POST 'http://localhost:8000/api/v1/wardrobe/upload' \\")
    print("  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
    print("  -F 'file=@test_images/01_white_tshirt.jpg'")
    print()
    print("Step 3: List your wardrobe items")
    print("curl -X GET 'http://localhost:8000/api/v1/wardrobe/items' \\")
    print("  -H 'Authorization: Bearer YOUR_JWT_TOKEN'")
    print()
    print("💡 Tip: Upload items from different categories to test outfit creation!")
    print()

    return downloaded_files

if __name__ == "__main__":
    main()
