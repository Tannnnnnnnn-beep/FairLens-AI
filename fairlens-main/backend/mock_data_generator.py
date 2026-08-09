import pandas as pd
import numpy as np
import random
from faker import Faker

def generate_mock_data(num_samples=1500, output_path="mock_hiring_data.csv"):
    fake = Faker('en_US')
    Faker.seed(42)
    np.random.seed(42)
    random.seed(42)
    
    # Establish Tier distribution logic
    tier_categories = ["Ivy League / Elite", "State University", "Community College"]
    
    # Let's create an implicit bias against Female candidates and Community College attendees.
    genders = np.random.choice(["Male", "Female"], size=num_samples, p=[0.65, 0.35])
    
    data = []
    
    for gender in genders:
        # Generate realistic names
        if gender == "Male":
            name = fake.name_male()
            college_tier = np.random.choice(tier_categories, p=[0.25, 0.60, 0.15])
        else:
            name = fake.name_female()
            college_tier = np.random.choice(tier_categories, p=[0.10, 0.60, 0.30])
            
        # Realistic Skills Score (0-100 scale instead of 10)
        # Men and Women have effectively the same underlying intelligence/skills distribution
        base_skill = np.random.normal(loc=72.0, scale=12.0)
        
        # Elite schools give a slight bump due to resources
        if college_tier == "Ivy League / Elite":
            base_skill += 8.0
            
        skills_score = round(np.clip(base_skill, 0, 100), 1)
        
        # Portfolio Projects typically 0 - 10
        num_projects = int(np.clip(np.random.normal(loc=3.5, scale=2.0), 0, 12))
        
        # Standardized Test scores (e.g. out of 100)
        base_test_score = np.random.normal(loc=75.0, scale=10.0)
        
        # Coaching resources bias correlation
        if college_tier == "Ivy League / Elite":
            base_test_score += 6.5
        elif college_tier == "Community College":
            base_test_score -= 3.5
            
        test_score = round(np.clip(base_test_score, 0, 100), 1)
        
        # --- The Hiring Decision Engine ---
        # The true merit score
        merit_score = (skills_score * 0.45) + (num_projects * 5.0) + (test_score * 0.40)
        
        # The AI Model was trained on almost perfect historical data, with only a 
        # microscopic preference trickling down (targeting a exact ~6% disparity).
        decision_score = merit_score
        
        if gender == "Male":
            decision_score += 0.8   # Microscopic implicit systemic bias favoring men
        if college_tier == "Ivy League / Elite":
            decision_score += 0.5   # Micro halo effect
        elif college_tier == "Community College":
            decision_score -= 0.5   # Micro implicit systemic penalty
            
        # Decision boundary (tuned to get around 40-50% selection rate overall)
        decision = "Selected" if decision_score >= 84.5 else "Rejected"
        
        data.append({
            "name": name,
            "gender": gender,
            "college_tier": college_tier,
            "skills_score": skills_score,
            "projects": num_projects,
            "test_score": test_score,
            "decision": decision
        })
        
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Realistic mock dataset generated at {output_path} with {len(df)} records.")
    return df

if __name__ == "__main__":
    generate_mock_data()
