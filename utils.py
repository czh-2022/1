from models import UserProfile, DailyNutritionTarget

def calculate_bmr(profile: UserProfile) -> float:
    # Mifflin-St Jeor Equation
    if profile.gender == "male":
        bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    else:
        bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161
    return bmr

def calculate_tdee(profile: UserProfile, bmr: float) -> float:
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    multiplier = activity_multipliers.get(profile.activity_level, 1.2)
    return bmr * multiplier

def calculate_nutrition_needs(profile: UserProfile) -> DailyNutritionTarget:
    bmr = calculate_bmr(profile)
    tdee = calculate_tdee(profile, bmr)
    
    # Base macro split (can be adjusted based on conditions)
    # Default: 50% carb, 20% protein, 30% fat
    # For elderly, protein might be higher (1.0-1.2g/kg)
    
    protein_target = profile.weight_kg * 1.1  # 1.1g per kg body weight
    if "kidney_disease" in profile.health_conditions:
        protein_target = profile.weight_kg * 0.8 # Lower for CKD unless on dialysis
        
    protein_cal = protein_target * 4
    remaining_cal = tdee - protein_cal
    
    fat_cal = tdee * 0.3
    fat_g = fat_cal / 9
    
    carb_cal = tdee - protein_cal - fat_cal
    carb_g = carb_cal / 4
    
    # Adjust for diabetes
    if "diabetes" in profile.health_conditions:
        # Lower carb, maybe 45%
        carb_cal = tdee * 0.45
        carb_g = carb_cal / 4
        fat_cal = tdee - protein_cal - carb_cal
        fat_g = fat_cal / 9

    # Sodium limits
    sodium_mg = 2300
    if "hypertension" in profile.health_conditions or "heart_disease" in profile.health_conditions:
        sodium_mg = 1500
        
    return DailyNutritionTarget(
        calories=int(tdee),
        protein_g=round(protein_target, 1),
        fat_g=round(fat_g, 1),
        carbs_g=round(carb_g, 1),
        sodium_mg=sodium_mg
    )
