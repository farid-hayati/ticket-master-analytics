import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from models import Attraction, Venue, Event
import psycopg2
from tqdm import tqdm

load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT"))
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

tixmaster_key = os.getenv("TIX_MASTER_API_KEY")
base_url = "https://app.ticketmaster.com/discovery/v2/events"
start_page = 130
end_page = 140
page_size = 10
start_date = "2026-06-01T00:00:00Z"

# Extract
def get_data(page):
    url = f"{base_url}?apikey={tixmaster_key}&locale=*&startDateTime={start_date}&page={page}&size={page_size}&sort=date,asc"
    # url = f"{base_url}?apikey={tixmaster_key}&locale=*&startDateTime={start_date}&size={page_size}&sort=date,asc"
    response = requests.get(url)

    if response.status_code == 200:
        events_json = response.json()
        return events_json
    else:
        print(f"Failed to retrieve data {response.status_code}")

# Transform 
def transform_data(raw_json: Dict[str, Any]):
    events: List[Event] = []
    venues_dict: Dict[str, Venue] = {}
    attractions_dict: Dict[str, Attraction] = {}

    raw_events = raw_json.get("_embedded", {}).get("events", [])

    for item in raw_events:
        # --- 1. Parse Venue ---
        venue_id = None
        venue_item = item.get("_embedded", {}).get("venues", [])
        if venue_item:
            v = venue_item[0]
            venue_id = v.get("id")

            # only save if new venue_id
            if venue_id and venue_id not in venues_dict:
                venues_dict[venue_id] = Venue(
                    venue_id=venue_id,
                    name=v.get("name"),
                    city=v.get("city", {}).get("name"),
                    state=v.get("state", {}).get("stateCode"),
                    country=v.get("country", {}).get("countryCode"),
                    postal_code=v.get("postalCode"),
                    longitude=v.get("location", {}).get("longitude"),
                    latitude=v.get("location", {}).get("latitude")
                )

        # --- 2. Parse Attraction ---
        attraction_id = None
        attraction_item = item.get("_embedded", {}).get("attractions", [])
        if attraction_item:
            for a in attraction_item:
            # a = attraction_item[0]
                attraction_id = a.get("id")

                # only save if new att_id
                if attraction_id and attraction_id not in attractions_dict:
                    # att_classifications = item.get("classifications", [{}])[0] if item.get("classifications") else {}
                    att_classifications = (item.get("classifications") or [{}])[0]
                    segment_name = (att_classifications.get("segment") or {}).get("name")
                    genre_name = (att_classifications.get("genre") or {}).get("name")
                    subgenre_name = (att_classifications.get("subGenre") or {}).get("name")

                    attractions_dict[attraction_id] = Attraction(
                        attraction_id=attraction_id,
                        name=a.get("name"),
                        # segment=segment_dict.get("name"),
                        # genre=genre_dict.get("name"),
                        # subgenre=subgenre_dict.get("name"),
                        segment=segment_name,
                        genre=genre_name,
                        subgenre=subgenre_name
                    )

        # --- 3. Parse Event ---
        price_ranges = item.get("priceRanges", [{}])[0]

        # classifications = item.get("classifications", [{}])[0] if item.get("classifications") else {}
        # segment_dict = classifications.get("segment") or {}
        # genre_dict = classifications.get("genre") or {}
        # subgenre_dict = classifications.get("subGenre") or {}

        classifications = (item.get("classifications") or [{}])[0]
        genre_name = (classifications.get("genre") or {}).get("name")
        segment_name = (classifications.get("segment") or {}).get("name")
        subgenre_name = (classifications.get("subGenre") or {}).get("name")

        events.append(Event(
            event_id=item.get("id"),
            name=item.get("name"),
            date=item.get("dates").get("start").get("dateTime"),
            venue_id=venue_id,
            attraction_id=attraction_id,
            min_price=price_ranges.get("min"),
            max_price=price_ranges.get("max"),
            # segment=segment_dict.get("name"),
            # genre=genre_dict.get("name"),
            # subgenre=subgenre_dict.get("name"),
            segment=segment_name,
            genre=genre_name,
            subgenre=subgenre_name,
            status=item.get("dates").get("status").get("code"),
            date_on_sale=item.get("sales").get("public").get("startDateTime") if item.get("sales") else None
        ))

    return events, list(venues_dict.values()), list(attractions_dict.values())

# Load
def load_data(events: List[Event], venues: List[Venue], attractions: List[Attraction]):
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )
    cursor = conn.cursor()

    for v in venues:
        cursor.execute("""
            INSERT INTO venues VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (venue_id) DO NOTHING;
        """, (v.venue_id, v.name, v.city, v.state, v.country, v.postal_code, v.longitude, v.latitude))

    for a in attractions:
        cursor.execute("""
            INSERT INTO attractions VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (attraction_id) DO NOTHING;
        """, (a.attraction_id, a.name, a.segment, a.genre, a.subgenre))

    for e in events:
        cursor.execute("""
            INSERT INTO events VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE SET
                min_price = EXCLUDED.min_price,
                max_price = EXCLUDED.max_price,
                date = EXCLUDED.date,
                status = EXCLUDED.status;
        """, (e.event_id, e.name, e.date, e.min_price, e.max_price, e.segment, e.genre, e.subgenre, e.venue_id, e.attraction_id, e.status, e.date_on_sale))

    conn.commit()
    conn.close()

# Run pipeline
def run_pipeline():
    for page in tqdm(range(start_page, end_page), desc="Processing Tix Master Pages"):
        raw_data = get_data(page)
        if raw_data:
            events, venues, attractions = transform_data(raw_data)
            load_data(events, venues, attractions)
    print("Pipeline finished successfully!")

if __name__ == "__main__":
    run_pipeline()