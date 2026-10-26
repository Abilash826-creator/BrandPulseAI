"""
Dataset generator script for Sree Annapoorna Restaurant (Coimbatore, Tamil Nadu).
Generates authentic Instagram dataset with food Reels, spoken transcripts, customer reviews,
and granular aspect ratings for Sree Annapoorna Coimbatore.
"""

import os
import json
import csv
import random
import datetime

def generate_annapoorna_dataset():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "app", "datasets", "annapoorna_coimbatore")
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "annapoorna_instagram_dataset.json")
    csv_path = os.path.join(output_dir, "annapoorna_instagram_dataset.csv")

    locations = ["RS Puram", "Gandhipuram", "Avinashi Road", "Peoples Park", "Mettupalayam Road", "Ganapathy"]
    
    # Authentic Instagram & food reviewer post templates
    templates = [
        # Ghee Roast & Dosa
        {
            "text": "Nothing beats the iconic Ghee Roast Dosa at Sree Annapoorna {loc} branch! Crispy, golden, piping hot with that heavenly aroma of pure ghee. 🤤🔥 #Annapoorna #CoimbatoreFood #GheeRoast #SouthIndianFood",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Ghee Roast",
            "aspect": "food_taste", "aspect_sentiment": "positive", "media_type": "REEL",
            "transcript": "Look at the golden crisp texture of this Annapoorna Ghee Roast. The aroma of pure melted ghee hitting the hot dosa pan is legendary in Coimbatore."
        },
        {
            "text": "Tried the Podi Ghee Roast and Rava Dosa at Annapoorna RS Puram today. Perfectly roasted and the coconut chutney was freshly ground! 🌟 #SreeAnnapoorna #CoimbatoreEats #DosaLovers",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Rava Dosa",
            "aspect": "food_taste", "aspect_sentiment": "positive", "media_type": "IMAGE",
            "transcript": None
        },
        {
            "text": "The Ghee Roast today at {loc} felt a bit soggy and not as crisp as usual. Hope the kitchen maintains the standard! 😕 #Annapoorna #FoodReview",
            "sentiment": "negative", "emotion": "sadness", "intent": "complaint", "product": "Ghee Roast",
            "aspect": "food_taste", "aspect_sentiment": "negative", "media_type": "POST",
            "transcript": None
        },

        # Filter Coffee
        {
            "text": "Starting my Coimbatore morning with Annapoorna's world-famous Filter Coffee. The froth, the aroma, the exact chicory balance — absolute perfection! ☕✨ #AnnapoornaCoffee #FilterCoffee #CoimbatoreVibes",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Filter Coffee",
            "aspect": "filter_coffee", "aspect_sentiment": "positive", "media_type": "REEL",
            "transcript": "Pouring the signature Annapoorna filter coffee in the traditional brass dabarah and tumbler. That thick frothy layer is unbeatable."
        },
        {
            "text": "Is there any coffee in Tamil Nadu better than Sree Annapoorna filter coffee? The degree blend is consistently top notch for 50+ years. ☕🏆 #SreeAnnapoorna #BestCoffee",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Filter Coffee",
            "aspect": "filter_coffee", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },
        {
            "text": "Ordered filter coffee at {loc} takeaway counter and it was barely warm. Temperature could have been hotter. #AnnapoornaCoffee",
            "sentiment": "negative", "emotion": "sadness", "intent": "complaint", "product": "Filter Coffee",
            "aspect": "filter_coffee", "aspect_sentiment": "negative", "media_type": "POST",
            "transcript": None
        },

        # Sambar & Vada
        {
            "text": "Annapoorna's Sambar Vada is unmatched in Coimbatore. Sambar is rich with shallots and freshly ground spices, vada is crispy yet soft inside! 🥣🧆 #SambarVada #Annapoorna #CoimbatoreFood",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Sambar Vada",
            "aspect": "sambar_flavor", "aspect_sentiment": "positive", "media_type": "REEL",
            "transcript": "Dipping the crispy medu vada directly into the hot bowl of signature Annapoorna sambar. You can taste the authentic drumstick and shallot essence."
        },
        {
            "text": "The sambar recipe here is pure heritage. Subtle sweetness and balanced spices make every dip of idli unforgettable! 🍲 #SreeAnnapoorna",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Idli Sambar",
            "aspect": "sambar_flavor", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },

        # Meals & Thali
        {
            "text": "Traditional South Indian Full Meals at Sree Annapoorna Gandhipuram. Kootu, poriyal, rasam, payasam and appalam on plantain leaf. 10/10 comfort food! 🌿🍛 #AnnapoornaMeals #CoimbatoreLunch",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Meals",
            "aspect": "food_taste", "aspect_sentiment": "positive", "media_type": "REEL",
            "transcript": "Full traditional banana leaf lunch feast at Annapoorna. Unlimited rice served with hot ghee, sambar, garlic rasam, and elaneer payasam."
        },
        {
            "text": "The curd rice and more kuzhambu during Sunday lunch at {loc} were exceptional. Generous portions and quick refills. 🍚✨ #Annapoorna",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Meals",
            "aspect": "food_taste", "aspect_sentiment": "positive", "media_type": "IMAGE",
            "transcript": None
        },

        # Sweets & Mysurpa
        {
            "text": "Brought a box of Annapoorna Ghee Mysurpa and Kaju Katli for Diwali. Melts in the mouth instantly! Premium quality sweets. 🍬🥮 #AnnapoornaSweets #Mysurpa #Coimbatore",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Mysurpa",
            "aspect": "food_taste", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },

        # Service, Waiting Time & Parking (Critical Real-World Friction Dimensions)
        {
            "text": "Huge waiting time at Annapoorna RS Puram on Sunday morning. Stood in queue for 45 minutes for a table! Food was great but management needs a better token queue system. ⏳ #WaitingQueue #RSpuram",
            "sentiment": "negative", "emotion": "anger", "intent": "complaint", "product": "Ghee Roast",
            "aspect": "waiting_time", "aspect_sentiment": "negative", "media_type": "REEL",
            "transcript": "Huge crowd waiting outside Annapoorna RS Puram this morning. The token wait time is currently 45 minutes for AC dining hall."
        },
        {
            "text": "Parking at the {loc} branch during peak evening dinner hours is a nightmare! No valet available and main road was congested. 🚗⚠️ #AnnapoornaParking #CoimbatoreTraffic",
            "sentiment": "negative", "emotion": "anger", "intent": "complaint", "product": "Meals",
            "aspect": "parking_access", "aspect_sentiment": "negative", "media_type": "POST",
            "transcript": None
        },
        {
            "text": "Outstanding service by the staff at Annapoorna {loc}. Attended to our large family gathering with utmost courtesy and speed. Kudos! 👏 #GreatService",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Meals",
            "aspect": "service_speed", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },
        {
            "text": "Table service was extremely slow today at {loc}. Waited 25 minutes just to get water and the menu card after getting seated. 😤 #SlowService #Annapoorna",
            "sentiment": "negative", "emotion": "anger", "intent": "complaint", "product": "Rava Dosa",
            "aspect": "service_speed", "aspect_sentiment": "negative", "media_type": "POST",
            "transcript": None
        },
        {
            "text": "Super clean dining hall, sanitized steel tumblers, and quick table turnover at Annapoorna Avinashi Road. High hygiene standards! 🧼✨ #Hygiene #Annapoorna",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Idli Sambar",
            "aspect": "cleanliness_hygiene", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },

        # Pricing & Value
        {
            "text": "Pricing has gone up recently on dosas and coffee, but the quality and taste consistency still justify the price tag. Pure heritage value! 💰👌 #ValueForMoney #Annapoorna",
            "sentiment": "positive", "emotion": "joy", "intent": "praise", "product": "Ghee Roast",
            "aspect": "pricing_value", "aspect_sentiment": "positive", "media_type": "POST",
            "transcript": None
        },
        {
            "text": "Rs. 140 for a single special roast feels a bit high compared to other local vegetarian eateries. Taste is good though. #PricingFeedback",
            "sentiment": "neutral", "emotion": "surprise", "intent": "query", "product": "Ghee Roast",
            "aspect": "pricing_value", "aspect_sentiment": "neutral", "media_type": "POST",
            "transcript": None
        },

        # General / Community Inquiry
        {
            "text": "Planning to visit Coimbatore next week. Which Annapoorna branch is best for family breakfast? RS Puram or People's Park? 🗺️🍳 #CoimbatoreTravel #FoodieQuery",
            "sentiment": "neutral", "emotion": "surprise", "intent": "query", "product": "Filter Coffee",
            "aspect": "service_speed", "aspect_sentiment": "neutral", "media_type": "POST",
            "transcript": None
        }
    ]

    authors = [
        {"name": "Coimbatore Foodie Guy", "handle": "@cbe_foodie_hub", "followers": 74000},
        {"name": "Tamilnadu Food Walk", "handle": "@tn_foodwalks", "followers": 125000},
        {"name": "Nandhini Gourmet", "handle": "@nandhini_tastes", "followers": 38000},
        {"name": "Karthik Subramanian", "handle": "@karthik_eats_cbe", "followers": 19500},
        {"name": "Kongu Food Diaries", "handle": "@kongu_flavor_trails", "followers": 89000},
        {"name": "Ananya Krishnan", "handle": "@ananya_foodtravel", "followers": 42000},
        {"name": "Coimbatore Daily Bites", "handle": "@cbedailybites", "followers": 61000},
        {"name": "Pravin Kumar", "handle": "@pravin_reviews", "followers": 15200}
    ]

    dataset_records = []
    base_date = datetime.datetime.now()

    # Generate 360 realistic labeled items across 30 days
    for i in range(360):
        tmpl = random.choice(templates)
        loc = random.choice(locations)
        auth = random.choice(authors)
        days_ago = random.randint(0, 30)
        post_time = base_date - datetime.timedelta(days=days_ago, hours=random.randint(1, 23), minutes=random.randint(1, 59))
        
        text_content = tmpl["text"].format(loc=loc)
        transcript = tmpl["transcript"]
        if transcript and "{loc}" in transcript:
            transcript = transcript.format(loc=loc)

        media_type = tmpl["media_type"]
        post_shortcode = f"C8annapoorna{1000 + i}"
        comment_id = None
        
        # Include specific public comments on posts
        if i % 3 == 0:
            media_type = "COMMENT"
            comment_id = f"180{random.randint(10000000, 99999999)}"
            url = f"https://www.instagram.com/p/{post_shortcode}/c/{comment_id}/"
        elif media_type == "REEL":
            url = f"https://www.instagram.com/reel/{post_shortcode}/"
        else:
            url = f"https://www.instagram.com/p/{post_shortcode}/"

        item = {
            "id": f"annapoorna_ig_{1000 + i}",
            "post_id": post_shortcode,
            "comment_id": comment_id,
            "brand": "Sree Annapoorna",
            "branch_location": loc,
            "platform": "instagram",
            "author": auth["name"],
            "author_handle": auth["handle"],
            "author_followers": auth["followers"] + random.randint(-500, 2500),
            "content": text_content,
            "text": text_content,
            "sentiment": tmpl["sentiment"],
            "emotion": tmpl["emotion"],
            "intent": tmpl["intent"],
            "product": tmpl["product"],
            "aspect": tmpl["aspect"],
            "aspect_sentiment": tmpl["aspect_sentiment"],
            "media_type": media_type,
            "transcript": transcript if media_type == "REEL" else None,
            "media_analysis_available": bool(transcript and media_type == "REEL"),
            "media_analysis_status": "transcript_analyzed" if (transcript and media_type == "REEL") else ("media_analysis_unavailable" if media_type == "REEL" else "not_video"),
            "like_count": random.randint(15, 8500),
            "comments_count": random.randint(0, 480),
            "url": url,
            "timestamp": post_time.isoformat()
        }
        dataset_records.append(item)

    # Save to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset_records, f, indent=2, ensure_ascii=False)

    # Save to CSV
    keys = ["id", "brand", "branch_location", "platform", "author", "author_handle", "author_followers", "text", "sentiment", "emotion", "intent", "product", "aspect", "aspect_sentiment", "media_type", "transcript", "like_count", "comments_count", "timestamp", "url"]
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(dataset_records)

    print(f"Generated Sree Annapoorna Coimbatore Instagram Dataset: {len(dataset_records)} records.")
    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV:  {csv_path}")
    return dataset_records

if __name__ == "__main__":
    generate_annapoorna_dataset()
