"""Seed script for Firestore database for FitPulse AI Coach."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-36a450e6f424"

EXERCISES_SEED = [
    {
        "id": "push-up",
        "name": "Push-up",
        "target_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Shoulders"],
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "description": "A classic upper body bodyweight exercise targeting chest, shoulders, and triceps.",
        "recommended_sets": "3 sets of 10-15 reps"
    },
    {
        "id": "barbell-squat",
        "name": "Barbell Back Squat",
        "target_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Core"],
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "description": "Fundamental compound leg movement building lower body strength and power.",
        "recommended_sets": "4 sets of 8-12 reps"
    },
    {
        "id": "dumbbell-bench-press",
        "name": "Dumbbell Bench Press",
        "target_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Anterior Deltoid"],
        "equipment": "Dumbbells",
        "difficulty": "Intermediate",
        "description": "Chest pressing exercise allowing independent unilateral arm movement and deep stretch.",
        "recommended_sets": "3 sets of 8-12 reps"
    },
    {
        "id": "pull-up",
        "name": "Pull-up",
        "target_muscle": "Back",
        "secondary_muscles": ["Biceps", "Forearms"],
        "equipment": "Bodyweight",
        "difficulty": "Intermediate",
        "description": "Upper body pulling exercise targeting the latissimus dorsi and biceps.",
        "recommended_sets": "3 sets of 5-10 reps"
    },
    {
        "id": "plank",
        "name": "Plank",
        "target_muscle": "Core",
        "secondary_muscles": ["Abs", "Obliques", "Lower Back"],
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "description": "Isometric core stability exercise maintaining a straight body line.",
        "recommended_sets": "3 sets holding for 30-60 seconds"
    },
    {
        "id": "dumbbell-bicep-curl",
        "name": "Dumbbell Bicep Curl",
        "target_muscle": "Biceps",
        "secondary_muscles": ["Brachialis", "Forearms"],
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "description": "Isolation exercise for building upper arm bicep strength.",
        "recommended_sets": "3 sets of 12-15 reps"
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Seeding exercises into Firestore project '{PROJECT_ID}'...")
    collection_ref = db.collection("exercises")
    
    for exercise in EXERCISES_SEED:
        doc_id = exercise["id"]
        collection_ref.document(doc_id).set(exercise)
        print(f"  [+] Seeded exercise: {exercise['name']} (ID: {doc_id})")
        
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
