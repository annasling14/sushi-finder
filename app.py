import sqlite3

import db

import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request


load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
db.init_db()

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

PRICE_LEVELS = {
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}

def search_sushi(location):
    """Ask the Google Places API for sushi restaurants near a location."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # Only request the fields we use (this also keeps costs down)
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.rating,"
            "places.userRatingCount,places.priceLevel,places.googleMapsUri"
        ),
    }
    body = {"textQuery": f"sushi restaurants in {location}"}
    response = requests.post(SEARCH_URL, headers=headers, json=body, timeout=10)
    response.raise_for_status()  # turn HTTP errors into Python exceptions
    return response.json().get("places", [])

def score_restaurants(places, trust=50, baseline=4.0):
    """rank restaurants with a review-adjusted rating. 
    
    a 5 star restauraunt with 3 reviews shouldn't beat a 4.7 star restaurant with 
    2000 reviews. i pretend every place starts with 'trust' reviews at a 'baseline'
    rating, and then add its real reviews on top (called a "Bayesian average"). 
    places with a few reviews stay close to the baseline; but places with many reviews
    end up close to their actual rating."""

    rated = [p for p in places if p.get("rating")]

    results = []
    for p in rated:
        reviews = p.get("userRatingCount", 0)
        adjusted = (reviews * p["rating"] + trust * baseline) / (reviews + trust)
        results.append({
            "place_id": p["id"],
            "name": p["displayName"]["text"],
            "address": p.get("formattedAddress", ""),
            "rating": p["rating"],
            "reviews": reviews,
            "price": PRICE_LEVELS.get(p.get("priceLevel")),  # None if unknown
            "score": round(adjusted, 2),
            "maps_url": p.get("googleMapsUri"),
        })

    return sorted(results, key = lambda r: r["score"], reverse=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    location = request.args.get("location", "").strip()
    if not location:
        return render_template("index.html", error="enter a city or neighborhood to search")

    try:
        places = search_sushi(location)
    except requests.RequestException as e:
        print("API key loaded:", API_KEY is not None)
        print("Error:", e)
        if e.response is not None:
            print("google says:", e.response.text)
        return render_template(
            "index.html",
            error = "couldn't reach google places. check ur API key & internet connection.",
        )
    results = score_restaurants(places)

    try:
        db.save_results(location, results)
    except sqlite3.Error as e:
        print("Couldn't save search:", e)

    return render_template("results.html", location=location, results=results)

if __name__ == "__main__":
    app.run(debug=True)
