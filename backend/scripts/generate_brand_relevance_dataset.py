import os
import csv
import random
import pandas as pd
from sklearn.model_selection import train_test_split

def generate_dataset():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    raw_dir = os.path.join(base_dir, "datasets", "brand_relevance", "raw")
    proc_dir = os.path.join(base_dir, "datasets", "brand_relevance", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)

    samples = [
        # ==========================================
        # 1. APPLE (PRODUCT BUSINESS)
        # ==========================================
        # Direct True Mentions (Positive / Praise)
        ("I love my new iPhone.", "Apple", "iPhone", 1, 1),
        ("The iPhone camera is excellent and takes crisp photos.", "Apple", "iPhone", 1, 1),
        ("Apple launched a new iPhone with stellar battery life.", "Apple", "iPhone", 1, 1),
        ("Just upgraded to the M3 MacBook Pro and the speed is unbelievable.", "Apple", "MacBook", 1, 1),
        ("Apple Watch series 10 heart monitoring saved my uncle's life.", "Apple", "Apple Watch", 1, 1),
        ("The iPad Pro OLED display is by far the best tablet screen in 2026.", "Apple", "iPad", 1, 1),
        ("Apple customer service was very helpful and replaced my screen in an hour.", "Apple", "Customer Support", 1, 1),
        ("Apple Pay makes checkout in supermarkets effortless.", "Apple", "Apple Pay", 1, 1),
        ("Loving iOS 18 on my iPhone 16! Apple Intelligence tools are super clean.", "Apple", "iPhone", 1, 1),
        ("AirPods Pro noise cancellation is unbeatable on long flights.", "Apple", "AirPods", 1, 1),
        ("Got my new Mac Mini M4. Incredible performance per dollar from Apple.", "Apple", "Mac Mini", 1, 1),
        ("The dynamic island on iPhone is actually super convenient for timer tracking.", "Apple", "iPhone", 1, 1),
        
        # Direct True Mentions (Complaints / Issues)
        ("My iPhone battery dies within two hours after updating to the latest iOS.", "Apple", "iPhone", 1, 1),
        ("My iPhone battery is terrible.", "Apple", "iPhone", 1, 1),
        ("Apple Pay isn't working today at any contactless terminal.", "Apple", "Apple Pay", 1, 1),
        ("Why does the iPhone 15 Pro get so hot while fast charging?", "Apple", "iPhone", 1, 1),
        ("Apple trade-in valuation offered peanuts for my MacBook Air.", "Apple", "MacBook", 1, 1),
        ("The iPad keyboard folio broke after only 3 months of normal use.", "Apple", "iPad", 1, 1),
        ("AirPods disconnect randomly during Zoom calls on MacOS.", "Apple", "AirPods", 1, 1),
        ("Apple App Store rejected our production build with vague guidelines.", "Apple", "App Store", 1, 1),
        ("Apple customer service refused my warranty claim for water resistance failure.", "Apple", "Customer Support", 1, 1),
        ("iCloud storage pricing is exorbitant compared to Google Drive.", "Apple", "iCloud", 1, 1),
        
        # Direct True Mentions (Neutral / Inquiries / Hashtags)
        ("Is anyone upgrading from iPhone 13 to iPhone 16 this September? #iPhone", "Apple", "iPhone", 1, 1),
        ("Comparing Apple Vision Pro spatial computing specs with Meta Quest.", "Apple", "Vision Pro", 1, 1),
        ("Does Apple Watch support offline Spotify playlists without cellular?", "Apple", "Apple Watch", 1, 1),
        ("Apple keynote scheduled for next Tuesday at Cupertino HQ.", "Apple", "Corporate", 1, 1),
        ("Does MacBook Air support dual external monitors natively?", "Apple", "MacBook", 1, 1),
        ("Check out this unboxing of the desert titanium iPhone 16 Pro Max.", "Apple", "iPhone", 1, 1),
        
        # Hard Negatives (Fruit / Cooking / Botany / Metaphors - Brand NOT Present & Irrelevant)
        ("I ate an apple yesterday for breakfast.", "Apple", "", 0, 0),
        ("Apple trees are beautiful in springtime when blossoms bloom.", "Apple", "", 0, 0),
        ("Apple pie is my favorite homemade dessert during Thanksgiving.", "Apple", "", 0, 0),
        ("I saw an apple tree near my house in the countryside.", "Apple", "", 0, 0),
        ("Making fresh apple cider with cinnamon and cloves for the autumn festival.", "Apple", "", 0, 0),
        ("An apple a day keeps the doctor away according to old folklore.", "Apple", "", 0, 0),
        ("Apple cider vinegar with warm water is great for morning digestion.", "Apple", "", 0, 0),
        ("Picked two baskets of crisp honeycrisp apples at the local orchard.", "Apple", "", 0, 0),
        ("Caramel apple slices make a delicious Halloween treat for kids.", "Apple", "", 0, 0),
        ("The apple orchard down the highway is open for picking this weekend.", "Apple", "", 0, 0),
        ("Apple sauce and roasted pork is a traditional Sunday roast pairing.", "Apple", "", 0, 0),
        ("She chopped fresh green apples into the summer walnut salad.", "Apple", "", 0, 0),

        # Competitor Context for Apple (Tracked Brand Apple -> Irrelevant or Competitor Only)
        ("I bought a Samsung Galaxy S24 Ultra and the zoom lens is unmatched.", "Apple", "", 0, 0),
        ("Google Pixel 9 Pro camera algorithms take much better night shots than rival phones.", "Apple", "", 0, 0),
        ("I bought a phone from another company.", "Apple", "", 0, 0),
        ("Xiaomi flagship charging speeds blow away American phone makers.", "Apple", "", 0, 0),
        ("Switched over to Asus ROG phone for dedicated gaming triggers.", "Apple", "", 0, 0),

        # ==========================================
        # 2. SAMSUNG (PRODUCT BUSINESS)
        # ==========================================
        ("Galaxy Buds have amazing sound quality and deep punchy bass.", "Samsung", "Galaxy Buds", 1, 1),
        ("Samsung Galaxy S24 Ultra anti-reflective screen is pure wizardry.", "Samsung", "Galaxy S series", 1, 1),
        ("Samsung customer service replaced my cracked Z Fold hinge under warranty.", "Samsung", "Customer Support", 1, 1),
        ("My Samsung Galaxy battery drains rapidly after the OneUI 6.1 patch.", "Samsung", "Galaxy S series", 1, 1),
        ("Samsung Smart TV interface is cluttered with sponsored bloatware.", "Samsung", "Smart TV", 1, 1),
        ("Loving the new Galaxy Watch Ultra battery longevity on hiking trails.", "Samsung", "Galaxy Watch", 1, 1),
        ("Samsung Knox security suite gives our enterprise fleet peace of mind.", "Samsung", "Knox", 1, 1),
        ("Galaxy Z Flip 6 crease is barely visible compared to last year's edition.", "Samsung", "Galaxy Z Flip", 1, 1),
        ("Samsung semiconductor foundry announced 2nm chip fabrication breakthrough.", "Samsung", "Semiconductors", 1, 1),
        ("The Galaxy Buds live case hinge feels loose after a few drops.", "Samsung", "Galaxy Buds", 1, 1),
        
        # Hard Negatives for Samsung (Astronomy / Galaxies / Metaphors)
        ("The Andromeda galaxy contains over one trillion stars in deep space.", "Samsung", "", 0, 0),
        ("Looking at distant galaxies through my backyard telescope tonight.", "Samsung", "", 0, 0),
        ("Guardians of the Galaxy is my all time favorite Marvel movie franchise.", "Samsung", "", 0, 0),
        ("The Milky Way galaxy spans roughly 100,000 light years in diameter.", "Samsung", "", 0, 0),

        # ==========================================
        # 3. SONY (PRODUCT BUSINESS)
        # ==========================================
        ("Sony WH-1000XM5 headphones have the best active noise canceling.", "Sony", "Headphones", 1, 1),
        ("PlayStation 5 Pro graphics rendering is breathtaking in 4K 60fps.", "Sony", "PlayStation", 1, 1),
        ("Sony Bravia OLED TV black levels are unmatched for movie nights.", "Sony", "Bravia", 1, 1),
        ("My Sony A7IV camera sensor overheated during a 4K 60p wedding shoot.", "Sony", "Alpha Camera", 1, 1),
        ("Sony DualSense controller stick drift happened after 6 months.", "Sony", "PlayStation", 1, 1),
        ("Sony Music Entertainment signed a massive streaming catalog licensing deal.", "Sony", "Music", 1, 1),
        ("The autofocus tracking on Sony G-Master lenses is instantaneous.", "Sony", "Alpha Camera", 1, 1),
        ("Sony PlayStation Network servers are undergoing scheduled maintenance.", "Sony", "PlayStation", 1, 1),
        
        # Hard Negatives for Sony / PS
        ("He is a bit sony and gloomy today in mood.", "Sony", "", 0, 0),
        ("Playing with ps post-script vector graphics in Adobe Illustrator.", "Sony", "", 0, 0),

        # ==========================================
        # 4. boAt (PRODUCT BUSINESS)
        # ==========================================
        ("boAt Airdopes 141 wireless earbuds provide solid bass for the price.", "boAt", "Airdopes", 1, 1),
        ("boAt Rockerz Bluetooth earphones mic quality is terrible in noisy traffic.", "boAt", "Rockerz", 1, 1),
        ("My boAt smartwatch display stopped turning on after swimming.", "boAt", "Smartwatch", 1, 1),
        ("boAt Stone speaker is super loud and waterproof for beach parties.", "boAt", "Stone Speaker", 1, 1),
        ("boAt customer support claimed warranty doesn't cover physical wire fraying.", "boAt", "Customer Support", 1, 1),
        ("Impressed by boAt Nirvana Ion 120 hour playback battery backup.", "boAt", "Nirvana Ion", 1, 1),
        
        # Hard Negatives for boAt (Watercraft / Boating / Nautical / Idioms)
        ("We took a small boat across the lake during our family picnic.", "boAt", "", 0, 0),
        ("Renting a wooden fishing boat this weekend for coastal trout angling.", "boAt", "", 0, 0),
        ("The cargo boat was sailing smoothly on the calm ocean waters.", "boAt", "", 0, 0),
        ("Row your boat gently down the stream merrily merrily life is a dream.", "boAt", "", 0, 0),
        ("We are all in the same boat when it comes to dealing with inflation.", "boAt", "", 0, 0),
        ("The speed boat crashed into the rocky shoreline during the storm.", "boAt", "", 0, 0),
        ("Docked the sailboat at the marina before sunset.", "boAt", "", 0, 0),

        # ==========================================
        # 5. NIKE (PRODUCT BUSINESS)
        # ==========================================
        ("Nike Air Jordan 1 retro high OG sneakers are absolute grails.", "Nike", "Air Jordan", 1, 1),
        ("Nike Pegasus 41 running shoes gave me painful blisters on my marathon run.", "Nike", "Pegasus", 1, 1),
        ("Nike Tech Fleece tracksuit is super comfortable for autumn weather.", "Nike", "Apparel", 1, 1),
        ("Nike SNKRS app crashed again right during the limited Travis Scott drop.", "Nike", "SNKRS App", 1, 1),
        ("Nike Dri-FIT training t-shirts wick away sweat effectively during workouts.", "Nike", "Dri-FIT", 1, 1),
        ("Nike customer care expedited my shoe replacement within 3 business days.", "Nike", "Customer Care", 1, 1),
        
        # Hard Negatives for Nike (Greek Mythology / Classical Art / History)
        ("Nike was the ancient Greek winged goddess who symbolized victory in battle.", "Nike", "", 0, 0),
        ("The famous ancient marble statue Winged Victory of Samothrace depicts Nike.", "Nike", "", 0, 0),
        ("Studying classical Greek mythology, specifically the deities Athena and Nike.", "Nike", "", 0, 0),
        ("The temple of Athena Nike stands proudly on the Athenian Acropolis.", "Nike", "", 0, 0),

        # ==========================================
        # 6. NETFLIX (SERVICE BUSINESS)
        # ==========================================
        ("Netflix keeps buffering during movies even on a high speed 500Mbps connection.", "Netflix", "Streaming", 1, 1),
        ("Loving the new season of Stranger Things on Netflix! Incredible CGI.", "Netflix", "Streaming", 1, 1),
        ("Netflix password sharing crackdown forced me to pay for an extra member slot.", "Netflix", "Subscription", 1, 1),
        ("Netflix 4K HDR subscription price hike is getting out of hand.", "Netflix", "Subscription", 1, 1),
        ("The Netflix recommendation algorithm suggested an amazing Korean thriller.", "Netflix", "Recommendation Engine", 1, 1),
        ("Netflix app UI on Apple TV is super responsive and seamless.", "Netflix", "Netflix App", 1, 1),
        ("Why does Netflix cancel fantastic original shows after just one season?", "Netflix", "Originals", 1, 1),
        ("Netflix offline download feature saved my 8-hour train journey.", "Netflix", "Offline Downloads", 1, 1),
        ("Binge watching documentary series on Netflix all weekend long.", "Netflix", "Streaming", 1, 1),
        
        # Hard Negatives for Netflix / Chill
        ("Let us chill on the couch and read vintage mystery novels tonight.", "Netflix", "", 0, 0),
        ("Streaming sunlight through the window warmed up the quiet living room.", "Netflix", "", 0, 0),

        # ==========================================
        # 7. SWIGGY (SERVICE BUSINESS)
        # ==========================================
        ("Swiggy delivery was 40 minutes late and the biryani arrived completely cold.", "Swiggy", "Delivery", 1, 1),
        ("Swiggy Instamart delivered my grocery order in under 11 minutes flat! Superb.", "Swiggy", "Instamart", 1, 1),
        ("Swiggy One membership saved me thousands in delivery fee charges this month.", "Swiggy", "Swiggy One", 1, 1),
        ("Swiggy delivery partner was extremely polite and handled delicate pastries with care.", "Swiggy", "Delivery", 1, 1),
        ("Swiggy customer executive refused refund for missing item in restaurant order.", "Swiggy", "Customer Support", 1, 1),
        ("Swiggy Dineout 30% discount on weekend dinner bill worked seamlessly.", "Swiggy", "Dineout", 1, 1),
        ("Swiggy app payment gateway failed but money was deducted from my bank account.", "Swiggy", "App & Payments", 1, 1),
        ("Ordering midnight snacks on Swiggy while finishing our engineering hackathon.", "Swiggy", "Delivery", 1, 1),
        
        # Hard Negatives for Swiggy (Idioms / Generic Food / Courier)
        ("I took a swig of cold water after my intense afternoon gym session.", "Swiggy", "", 0, 0),
        ("She took a quick swig of orange juice before running to catch the bus.", "Swiggy", "", 0, 0),
        ("Cooking homemade pasta with garlic and olive oil in my kitchen tonight.", "Swiggy", "", 0, 0),

        # ==========================================
        # 8. ZOMATO (SERVICE BUSINESS)
        # ==========================================
        ("Zomato Gold 1+1 food offers made dining out so much more affordable.", "Zomato", "Zomato Gold", 1, 1),
        ("Zomato delivery valet was caught on camera eating customer fries. Unacceptable!", "Zomato", "Delivery", 1, 1),
        ("Zomato instant refund credited to wallet in 30 seconds for spilt curry.", "Zomato", "Customer Support", 1, 1),
        ("Blinkit by Zomato delivered my urgent laptop charger in 8 minutes.", "Zomato", "Blinkit", 1, 1),
        ("Zomato app UI during IPL cricket live streaming had fun gamified discount games.", "Zomato", "App", 1, 1),
        ("Zomato high platform fee per order is annoying loyal customers.", "Zomato", "Pricing", 1, 1),
        
        # Hard Negatives for Zomato
        ("Tomato soup with toasted garlic croutons is comfort food on rainy days.", "Zomato", "", 0, 0),
        ("Harvested juicy red tomatoes from our rooftop vegetable garden.", "Zomato", "", 0, 0),

        # ==========================================
        # 9. UBER (SERVICE BUSINESS)
        # ==========================================
        ("Uber driver canceled the ride after making me wait for 15 minutes in heavy rain.", "Uber", "Uber Ride", 1, 1),
        ("Uber Eats delivered hot ramen noodles right to my hotel doorstep.", "Uber", "Uber Eats", 1, 1),
        ("Uber surge pricing of 3.5x during airport peak hours is pure daylight robbery.", "Uber", "Pricing", 1, 1),
        ("Uber Reserve pre-booked cab arrived 5 minutes early for my 4 AM flight.", "Uber", "Uber Reserve", 1, 1),
        ("Uber customer support refunded ride fare immediately after driver took wrong route.", "Uber", "Customer Support", 1, 1),
        ("Uber Green EV taxi was spotless and provided a smooth quiet ride.", "Uber", "Uber Green", 1, 1),
        ("Left my wallet in the Uber cab and the honest driver returned it within an hour.", "Uber", "Uber Ride", 1, 1),
        
        # Hard Negatives for Uber (Adjective / Prefix / General Idiom)
        ("He is an uber cool and stylish fashion designer in Milan.", "Uber", "", 0, 0),
        ("She was uber excited about attending the Taylor Swift concert tonight.", "Uber", "", 0, 0),
        ("That new science fiction video game looks uber realistic and immersive.", "Uber", "", 0, 0),
        ("The company culture is uber competitive among senior executives.", "Uber", "", 0, 0),
        ("Taking a regular city bus to the downtown library this afternoon.", "Uber", "", 0, 0),

        # ==========================================
        # 10. TCS (SERVICE BUSINESS - IT & CONSULTING)
        # ==========================================
        ("TCS secured a $1 billion cloud transformation deal with a major European bank.", "TCS", "Cloud Services", 1, 1),
        ("TCS BaNCS core banking platform processes millions of daily transactions smoothly.", "TCS", "BaNCS", 1, 1),
        ("TCS returned to office 5-day mandate caused dissatisfaction among senior developers.", "TCS", "Workplace", 1, 1),
        ("TCS AI studio launched new enterprise generative AI agents for manufacturing.", "TCS", "AI Studio", 1, 1),
        ("TCS quarterly revenue earnings beat Wall Street analyst expectations.", "TCS", "Corporate", 1, 1),
        ("Working with TCS consulting partners on our enterprise SAP S/4HANA migration.", "TCS", "Consulting", 1, 1),
        
        # Hard Negatives for TCS (Tax / Acronyms / Physics)
        ("The government announced changes to the Tax Collected at Source (TCS) rules.", "TCS", "", 0, 0),
        ("TCS tax deduction on foreign outward remittances increased to 20 percent.", "TCS", "", 0, 0),
        ("Total carbon substance (TCS) measurements in wastewater samples were normal.", "TCS", "", 0, 0),
        ("Theoretical Computer Science (TCS) research symposium proceedings published online.", "TCS", "", 0, 0),

        # ==========================================
        # GENERAL IRRELEVANT SOCIAL NOISE
        # ==========================================
        ("Going for a morning jog in Central Park before the sun gets too bright.", "", "", 0, 0),
        ("The weather today is cloudy with a 60% chance of afternoon thunderstorms.", "", "", 0, 0),
        ("Reading a fascinating novel about 19th century historical European architecture.", "", "", 0, 0),
        ("Cooking a three course dinner with friends this Saturday evening.", "", "", 0, 0),
        ("Looking for recommendations on great scenic hiking trails in Colorado.", "", "", 0, 0),
        ("Studying calculus formulas for tomorrow's university midterm exam.", "", "", 0, 0),
        ("Woke up early to watch the sunrise over the eastern horizon.", "", "", 0, 0),
        ("The traffic on the interstate highway was backed up for miles.", "", "", 0, 0),
        ("Coffee without sugar is the best way to kickstart a productive Monday.", "", "", 0, 0),
        ("Planting organic tomato and bell pepper seedlings in the garden beds.", "", "", 0, 0)
    ]

    # Expand dataset with realistic linguistic variations (typos, hashtags, informal phrasing)
    extended_samples = list(samples)
    
    variations = [
        # Apple variations
        ("iPhone 16 camera quality is genuinely mind blowing. Best smartphone camera yet!", "Apple", "iPhone", 1, 1),
        ("Cant believe how bad my iphone battery life has become after the 18.2 update.", "Apple", "iPhone", 1, 1),
        ("Apple genius bar technician resolved my keyboard issue in 10 mins flat.", "Apple", "Customer Support", 1, 1),
        ("Is apple care warranty actually worth buying for the new iPad Pro?", "Apple", "iPad", 1, 1),
        ("Baked fresh cinnamon apple turnovers for breakfast.", "Apple", "", 0, 0),
        ("Drinking chilled apple juice with crushed ice.", "Apple", "", 0, 0),
        ("Apple blossom festival in the valley was crowded this weekend.", "Apple", "", 0, 0),
        
        # Samsung variations
        ("Galaxy S24 zoom lens captured the moon craters with surreal clarity.", "Samsung", "Galaxy S series", 1, 1),
        ("My Samsung refrigerator ice maker stopped dispensing ice cubes.", "Samsung", "Appliances", 1, 1),
        ("Samsung TV remote control unpaired itself out of nowhere.", "Samsung", "Smart TV", 1, 1),
        ("The Andromeda galaxy spiral arms photographed with amateur astro gear.", "Samsung", "", 0, 0),
        
        # Service variations
        ("Netflix streaming resolution dropped to 480p despite fiber optic internet.", "Netflix", "Streaming", 1, 1),
        ("Swiggy food delivery guy braved heavy rain to bring our pizza order on time.", "Swiggy", "Delivery", 1, 1),
        ("Zomato delivery charges during midnight rain are ridiculously high.", "Zomato", "Delivery", 1, 1),
        ("Took an Uber Premier cab to the corporate summit. Very clean sedan.", "Uber", "Uber Ride", 1, 1),
        ("Uber driver refused to turn on AC during scorching afternoon heat.", "Uber", "Uber Ride", 1, 1),
        ("He is an uber talented guitarist playing at the local jazz lounge.", "Uber", "", 0, 0),
        ("TCS enterprise cloud consulting team helped us scale our microservices.", "TCS", "Cloud Services", 1, 1),
        ("Calculate 5% TCS on international credit card transactions above threshold.", "TCS", "", 0, 0)
    ]
    extended_samples.extend(variations)

    # Convert to DataFrame
    df = pd.DataFrame(extended_samples, columns=["text", "brand", "product", "brand_present", "relevant"])
    
    # Save raw CSV
    raw_csv_path = os.path.join(raw_dir, "brand_relevance_raw.csv")
    df.to_csv(raw_csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"[Dataset] Generated {len(df)} raw samples -> {raw_csv_path}")

    # Stratified Train/Val/Test Split (70% / 15% / 15%)
    # Stratify by combined target (brand_present, relevant)
    df["strat_key"] = df["brand_present"].astype(str) + "_" + df["relevant"].astype(str)
    
    train_df, temp_df = train_test_split(df, test_size=0.30, random_state=42, stratify=df["strat_key"])
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42, stratify=temp_df["strat_key"])

    # Drop strat_key
    train_df = train_df.drop(columns=["strat_key"])
    val_df = val_df.drop(columns=["strat_key"])
    test_df = test_df.drop(columns=["strat_key"])

    train_path = os.path.join(proc_dir, "train.csv")
    val_path = os.path.join(proc_dir, "validation.csv")
    test_path = os.path.join(proc_dir, "test.csv")

    train_df.to_csv(train_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    val_df.to_csv(val_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    test_df.to_csv(test_path, index=False, quoting=csv.QUOTE_NONNUMERIC)

    print(f"[Dataset] Processed splits:")
    print(f"  • Train: {len(train_df)} samples -> {train_path}")
    print(f"  • Validation: {len(val_df)} samples -> {val_path}")
    print(f"  • Test: {len(test_df)} samples -> {test_path}")

if __name__ == "__main__":
    generate_dataset()
