import pandas as pd

# Load both datasets
india_df = pd.read_csv("data/Top Indian Places to Visit.csv")
world_df = pd.read_csv("data/international_places.csv")

# ---- Standardize INDIA dataset ----
india_clean = pd.DataFrame({
    "place_name": india_df["Name"],
    "city": india_df["City"],
    "country": "India",
    "category": india_df["Significance"],
    "rating": india_df["Google review rating"],
    "cost": india_df["Entrance Fee in INR"],
    "description": (
        "A " + india_df["Type"].astype(str) + " site in " + india_df["City"].astype(str) +
        ", significant for " + india_df["Significance"].astype(str) +
        ". Best time to visit: " + india_df["Best Time to visit"].astype(str) +
        ". Takes about " + india_df["time needed to visit in hrs"].astype(str) + " hours."
    ) 
})

# ---- Standardize INTERNATIONAL dataset ----
world_clean = pd.DataFrame({
    "place_name": world_df["place_name"],
    "city": world_df["city"], 
    "country": world_df["country"],
    "category": world_df["category"],
    "rating": world_df["rating"],
    "cost": world_df["cost_usd"],  
    "description": world_df["description"]
})

# ---- Combine both ----
merged_df = pd.concat([india_clean, world_clean], ignore_index=True)
merged_df = merged_df.dropna(subset=["place_name"])

merged_df.to_csv("data/merged_places.csv", index=False)

print("Merge complete!")
print("Total rows:", len(merged_df))
print(merged_df.head(5)) 