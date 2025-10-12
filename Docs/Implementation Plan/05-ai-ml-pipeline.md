# AI/ML Pipeline Implementation

## Roboflow Integration

### app/services/ai/clothing_detection.py
```python
import httpx
from app.core.config import settings

async def detect_clothing(image_path: str) -> dict:
    url = f"https://detect.roboflow.com/{settings.ROBOFLOW_PROJECT}/{settings.ROBOFLOW_MODEL_ID}"

    with open(image_path, "rb") as f:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={"api_key": settings.ROBOFLOW_API_KEY},
                files={"file": f}
            )

    if response.status_code == 200:
        data = response.json()
        if data.get("predictions"):
            pred = data["predictions"][0]
            return {
                "category": pred.get("class"),
                "confidence": pred.get("confidence") * 100,
                "color": extract_color(image_path)
            }
    return {"category": "unknown", "confidence": 0}

def extract_color(image_path: str) -> str:
    from PIL import Image
    import numpy as np
    from sklearn.cluster import KMeans

    img = Image.open(image_path).convert('RGB')
    img = img.resize((150, 150))
    pixels = np.array(img).reshape(-1, 3)

    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(pixels)
    dominant = kmeans.cluster_centers_[0].astype(int)

    return rgb_to_name(dominant)
```

## Background Removal

### app/services/ai/background_removal.py
```python
from rembg import remove
from PIL import Image

def remove_background(input_path: str, output_path: str):
    with open(input_path, 'rb') as inp:
        input_data = inp.read()

    output_data = remove(input_data)

    with open(output_path, 'wb') as out:
        out.write(output_data)

    return output_path
```

## Weaviate Integration

### app/services/ai/embeddings.py
```python
import weaviate
from app.core.config import settings

client = weaviate.Client(url=f"http://{settings.WEAVIATE_HOST}:8080")

def init_schema():
    schema = {
        "class": "ClothingItem",
        "vectorizer": "text2vec-transformers",
        "properties": [
            {"name": "itemId", "dataType": ["string"]},
            {"name": "userId", "dataType": ["string"]},
            {"name": "category", "dataType": ["string"]},
            {"name": "color", "dataType": ["string"]},
            {"name": "description", "dataType": ["text"]}
        ]
    }
    client.schema.create_class(schema)

def add_item(item_id: str, user_id: str, category: str, color: str):
    description = f"{category} in {color}"
    client.data_object.create(
        data_object={
            "itemId": str(item_id),
            "userId": str(user_id),
            "category": category,
            "color": color,
            "description": description
        },
        class_name="ClothingItem"
    )

def search_items(query: str, user_id: str, limit: int = 10):
    result = (
        client.query
        .get("ClothingItem", ["itemId", "category", "color"])
        .with_hybrid(query=query)
        .with_where({
            "path": ["userId"],
            "operator": "Equal",
            "valueString": user_id
        })
        .with_limit(limit)
        .do()
    )
    return result["data"]["Get"]["ClothingItem"]
```

## Recommendation Algorithm

### app/services/recommendation/algorithm.py
```python
from typing import List
from uuid import UUID
from app.services.ai.embeddings import search_items
from app.services.external.weather_api import get_weather

def generate_outfits(user_id: UUID, location: str, event_type: str = "casual") -> List[dict]:
    weather = get_weather(location)
    temp = weather["temp"]

    # Temperature-based categories
    if temp > 25:
        base_cats = ["shorts", "skirt"]
        top_cats = ["t-shirt", "tank"]
    else:
        base_cats = ["jeans", "trousers"]
        top_cats = ["shirt", "sweater"]

    outfits = []
    for i in range(3):
        base_query = f"{base_cats[i % len(base_cats)]} {event_type}"
        bases = search_items(base_query, str(user_id), 3)

        top_query = f"{top_cats[i % len(top_cats)]} {event_type}"
        tops = search_items(top_query, str(user_id), 3)

        if bases and tops:
            outfits.append({
                "top": tops[0]["itemId"],
                "bottom": bases[0]["itemId"],
                "weather": weather
            })

    return outfits[:3]
```

## Weather API

### app/services/external/weather_api.py
```python
import httpx
from app.core.config import settings

async def get_weather(lat: float, lon: float) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return {
            "temp": data["main"]["temp"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"]
        }
    return {"temp": 25, "condition": "Clear"}
```

## Background Worker

### app/workers/image_processor.py
```python
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.ai.background_removal import remove_background
from app.services.ai.clothing_detection import detect_clothing
from app.services.ai.embeddings import add_item

async def process_wardrobe_image(image_path: str, user_id: UUID, db: Session):
    try:
        # Remove background
        processed = image_path.replace("originals", "processed")
        remove_background(image_path, processed)

        # Detect attributes
        detection = await detect_clothing(processed)

        # Add to Weaviate
        add_item(item_id, user_id, detection["category"], detection["color"])

        # Update database
        # ... (update wardrobe_item record)

    except Exception as e:
        print(f"Error: {e}")
```

**Estimated Time**: 1 week
