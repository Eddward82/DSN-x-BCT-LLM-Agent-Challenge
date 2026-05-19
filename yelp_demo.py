"""
yelp_demo.py
Reads real users from the Yelp dataset and demos the Task A and Task B API endpoints.

Usage:
    python yelp_demo.py

Requirements:
    pip install requests
"""

import json
import requests
import random
from collections import defaultdict

# ─── CONFIG ───
REVIEW_FILE = r"D:\yelp-data\yelp_academic_dataset_review.json"
BUSINESS_FILE = r"D:\yelp-data\yelp_academic_dataset_business.json"
API_BASE = "http://localhost:8000"
MIN_REVIEWS = 5       # minimum reviews a user must have to be selected
MAX_REVIEWS = 10      # cap how many past reviews we send per user
NUM_USERS = 3         # how many users to demo


def load_businesses(filepath, limit=50000):
    """Load businesses into a dict keyed by business_id."""
    print(f"Loading businesses...")
    businesses = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            try:
                b = json.loads(line)
                businesses[b["business_id"]] = b
            except:
                continue
    print(f"  Loaded {len(businesses):,} businesses")
    return businesses


def load_user_reviews(filepath, businesses, limit=500000):
    """Load reviews and group by user_id, filtering to known businesses."""
    print(f"Loading reviews (first {limit:,} lines)...")
    user_reviews = defaultdict(list)
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            try:
                r = json.loads(line)
                bid = r.get("business_id")
                if bid in businesses:
                    user_reviews[r["user_id"]].append(r)
            except:
                continue
    print(f"  Found {len(user_reviews):,} users with reviews")
    return user_reviews


def pick_users(user_reviews, businesses, n=3):
    """Pick n users who have enough reviews."""
    eligible = [
        uid for uid, reviews in user_reviews.items()
        if len(reviews) >= MIN_REVIEWS
    ]
    print(f"  {len(eligible):,} eligible users (min {MIN_REVIEWS} reviews)")
    selected = random.sample(eligible, min(n, len(eligible)))
    return selected


def build_persona(user_id, user_reviews, businesses, city="Philadelphia"):
    """Build a UserPersona dict from real Yelp data."""
    reviews = user_reviews[user_id][:MAX_REVIEWS]
    past_reviews = []
    for r in reviews:
        b = businesses.get(r["business_id"], {})
        categories = b.get("categories") or "Restaurant"
        if isinstance(categories, list):
            category = categories[0]
        else:
            category = str(categories).split(",")[0].strip()

        past_reviews.append({
            "business_name": b.get("name", "Unknown Business"),
            "category": category,
            "rating": float(r["stars"]),
            "review_text": r["text"][:300]  # truncate long reviews
        })

    return {
        "user_id": user_id[:8],
        "name": f"User_{user_id[:6]}",
        "city": city,
        "past_reviews": past_reviews
    }


def get_candidate_businesses(businesses, n=5):
    """Pick n random businesses to use as recommendation candidates."""
    sample = random.sample(list(businesses.values()), min(n * 10, len(businesses)))
    candidates = []
    for b in sample:
        if b.get("name") and b.get("categories"):
            categories = b.get("categories") or ""
            if isinstance(categories, list):
                category = categories[0]
            else:
                category = str(categories).split(",")[0].strip()
            candidates.append({
                "name": b["name"],
                "category": category,
                "price_range": str(b.get("attributes", {}).get("RestaurantsPriceRange2", "medium") or "medium"),
                "avg_rating": float(b.get("stars", 3.5)),
                "description": f"{b.get('name')} in {b.get('city', 'the city')}. Categories: {str(b.get('categories', ''))[:100]}"
            })
        if len(candidates) >= n:
            break
    return candidates


def demo_task_a(persona, target_business):
    """Call Task A endpoint and print result."""
    print(f"\n{'='*60}")
    print(f"TASK A — Simulating review for: {target_business['name']}")
    print(f"User: {persona['name']} from {persona['city']}")
    print(f"Past reviews: {len(persona['past_reviews'])}")
    print(f"{'='*60}")

    payload = {
        "user_persona": persona,
        "target_business": target_business["name"],
        "target_category": target_business["category"],
        "target_description": target_business["description"]
    }

    try:
        r = requests.post(f"{API_BASE}/task-a/simulate-review", json=payload, timeout=30)
        if r.status_code == 200:
            result = r.json()
            print(f"  Simulated Rating: {result['simulated_rating']} / 5.0")
            print(f"  Simulated Review: {result['simulated_review']}")
            print(f"  Agent Reasoning:  {result['reasoning']}")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  FAILED: {e}")


def demo_task_b(persona, candidates):
    """Call Task B endpoint and print result."""
    print(f"\n{'='*60}")
    print(f"TASK B — Recommendations for: {persona['name']} from {persona['city']}")
    print(f"Candidates: {len(candidates)} businesses")
    print(f"{'='*60}")

    payload = {
        "user_persona": persona,
        "context": "Looking for a good place to eat tonight",
        "available_businesses": candidates
    }

    try:
        r = requests.post(f"{API_BASE}/task-b/recommend", json=payload, timeout=30)
        if r.status_code == 200:
            result = r.json()
            print(f"  Agent Reasoning: {result['agent_reasoning'][:200]}...")
            print(f"\n  Ranked Recommendations:")
            for rec in result["recommendations"]:
                print(f"    #{rec['rank']} {rec['business_name']} — Predicted: {rec['predicted_rating']}/5")
                print(f"        {rec['reason'][:120]}")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  FAILED: {e}")


def main():
    print("\n DSN x BCT LLM Agent Challenge — Yelp Dataset Demo")
    print("="*60)

    # Load data
    businesses = load_businesses(BUSINESS_FILE)
    user_reviews = load_user_reviews(REVIEW_FILE, businesses)

    # Pick real users
    selected_users = pick_users(user_reviews, businesses, n=NUM_USERS)
    print(f"\nSelected {len(selected_users)} real Yelp users for demo\n")

    # Get candidate businesses for Task B
    candidates = get_candidate_businesses(businesses, n=5)

    # Run demo for each user
    for i, user_id in enumerate(selected_users):
        print(f"\n--- USER {i+1} of {len(selected_users)} ---")
        persona = build_persona(user_id, user_reviews, businesses)

        # Pick a business they haven't reviewed for Task A
        reviewed_ids = {r["business_id"] for r in user_reviews[user_id]}
        unseen = [b for bid, b in businesses.items() if bid not in reviewed_ids and b.get("name")]
        if unseen:
            target = random.choice(unseen[:100])
            categories = target.get("categories") or "Restaurant"
            category = str(categories).split(",")[0].strip()
            target_business = {
                "name": target["name"],
                "category": category,
                "description": f"{target['name']} in {target.get('city', 'the city')}. {str(target.get('categories', ''))[:100]}"
            }
            demo_task_a(persona, target_business)

        demo_task_b(persona, candidates)

    print(f"\n{'='*60}")
    print("Demo complete!")


if __name__ == "__main__":
    main()
