import datetime
from google.cloud import firestore
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

PROJECT_ID = "qwiklabs-gcp-01-36a450e6f424"
MEMORY_BANK_ID = "3103109885630349312"
BUCKET_NAME = "fitpulse-ai-coach-assets-qwiklabs-gcp-01-36a450e6f424"


def _get_db_client():
    return firestore.Client(project=PROJECT_ID)


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Note: add_session_to_memory skipped/failed: {e}")
    return None


def get_memory_service():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are FitPulse AI Coach, an expert personalized fitness and workout assistant. "
        "You help users search the exercise library, log completed workout sessions, review workout history, "
        "calculate health & energy metrics (BMI, BMR, TDEE, heart rate zones), lookup real nutrition facts for food items, "
        "and generate exercise illustrations using AI."
    ),
    workflow_description=(
        "Analyze the user's fitness request, call appropriate tools to gather data or generate illustrations, "
        "and return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the public URL returned by generate_exercise_image after uploading "
        "to Cloud Storage). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://storage.googleapis.com/..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


async def generate_exercise_image(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates an image illustrating an exercise or workout posture using AI.

    Args:
        prompt: Description of the exercise or workout image to generate (e.g., 'dumbbell bicep curl form', 'bodyweight squat posture').
        tool_context: ToolContext provided automatically by ADK for saving artifacts.

    Returns:
        The public HTTPS URL of the generated image stored in Cloud Storage.
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    res = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"A clear, high-quality fitness illustration showing: {prompt}",
    )

    img_part = None
    if res.candidates and res.candidates[0].content and res.candidates[0].content.parts:
        for part in res.candidates[0].content.parts:
            if part.inline_data:
                img_part = part
                break

    if not img_part:
        return f"Failed to generate image for prompt: '{prompt}'."

    image_bytes = img_part.inline_data.data
    mime_type = img_part.inline_data.mime_type or "image/jpeg"
    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"exercise_{uuid.uuid4().hex[:8]}.{ext}"

    # (1) Save artifact in ADK tool_context if provided
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save artifact in tool_context: {e}")

    # (2) Upload image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    return (
        f"Successfully generated exercise image!\n"
        f"Public URL: {public_url}\n"
        f"Markdown Image: ![{prompt}]({public_url})"
    )


async def generate_exercise_video(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates a short exercise demonstration video using Google's Omni model (gemini-omni-flash-preview).

    Args:
        prompt: Description of the exercise or workout technique to demonstrate in video (e.g., 'dumbbell bicep curl form', 'bodyweight squat posture').
        tool_context: ToolContext provided automatically by ADK for saving artifacts.

    Returns:
        The public HTTPS URL of the generated video stored in Cloud Storage.
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=f"Generate a short video demonstrating proper form for: {prompt}",
    )

    video_data = None
    if hasattr(res, "output_video") and res.output_video:
        ov = res.output_video
        if isinstance(ov, dict):
            video_data = ov.get("data")
        elif hasattr(ov, "data"):
            video_data = ov.data

    if not video_data and hasattr(res, "to_dict"):
        d = res.to_dict()
        video_data = d.get("output_video", {}).get("data")

    if not video_data:
        return f"Failed to generate video for prompt: '{prompt}'."

    if isinstance(video_data, str):
        video_bytes = base64.b64decode(video_data)
    elif isinstance(video_data, bytes):
        video_bytes = video_data
    else:
        return f"Failed to extract video bytes for prompt: '{prompt}'."

    filename = f"exercise_video_{uuid.uuid4().hex[:8]}.mp4"
    mime_type = "video/mp4"

    # (1) Save artifact in ADK tool_context if provided
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        except Exception as e:
            print(f"Warning: Failed to save video artifact in tool_context: {e}")

    # (2) Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    return (
        f"Successfully generated exercise video!\n"
        f"Public URL: {public_url}"
    )


def search_exercise_library(query: str = "", target_muscle: str = "") -> str:
    """Searches the exercise library in Firestore by exercise name, query, or target muscle group.

    Args:
        query: General search term or exercise name/type (e.g., 'press', 'squat', 'bodyweight').
        target_muscle: Target muscle group (e.g., 'Chest', 'Legs', 'Back', 'Biceps', 'Core').

    Returns:
        A formatted list of matching exercises with equipment, difficulty, and details.
    """
    db = _get_db_client()
    docs = db.collection("exercises").stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        name = data.get("name", "")
        t_muscle = data.get("target_muscle", data.get("muscle_group", "")).lower()
        sec_muscles = [m.lower() for m in data.get("secondary_muscles", [])]
        equip = data.get("equipment", "").lower()
        desc = data.get("description", data.get("instructions", ""))

        match = True
        if target_muscle:
            tm_lower = target_muscle.lower()
            if tm_lower not in t_muscle and not any(tm_lower in sm for sm in sec_muscles):
                match = False

        if query and match:
            q_lower = query.lower()
            if (
                q_lower not in name.lower()
                and q_lower not in t_muscle
                and q_lower not in equip
                and q_lower not in desc.lower()
            ):
                match = False

        if match:
            results.append(
                f"- **{name}** (Target: {data.get('target_muscle', 'N/A')})\n"
                f"  Equipment: {data.get('equipment')} | Difficulty: {data.get('difficulty')}\n"
                f"  Recommended Sets: {data.get('recommended_sets', 'N/A')}\n"
                f"  Description: {desc}"
            )

    if not results:
        return f"No exercises found matching query='{query}', target_muscle='{target_muscle}'."

    return "Found exercises:\n\n" + "\n\n".join(results)


def log_workout_session(
    exercise_name: str,
    sets: int,
    reps: int,
    weight_lbs: float = 0.0,
    user_id: str = "default_user",
) -> str:
    """Logs a completed exercise workout session to Firestore.

    Args:
        exercise_name: Name of the exercise performed (e.g., 'Push-up', 'Barbell Back Squat').
        sets: Number of sets completed.
        reps: Number of repetitions per set.
        weight_lbs: Weight used in pounds (0.0 for bodyweight exercises).
        user_id: Identifier for the user (defaults to 'default_user').

    Returns:
        A confirmation message with the logged workout details and timestamp.
    """
    db = _get_db_client()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log_entry = {
        "user_id": user_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "timestamp": now_iso,
    }

    doc_ref = db.collection("workout_logs").add(log_entry)
    doc_id = doc_ref[1].id

    return (
        f"Successfully logged workout for {user_id}:\n"
        f"- Exercise: {exercise_name}\n"
        f"- Sets x Reps: {sets} x {reps}\n"
        f"- Weight: {weight_lbs} lbs\n"
        f"- Log ID: {doc_id} (at {now_iso})"
    )


def get_user_workout_history(user_id: str = "default_user") -> str:
    """Retrieves past workout logs for a given user from Firestore.

    Args:
        user_id: Identifier for the user (defaults to 'default_user').

    Returns:
        A list of recent logged workout sessions for the user.
    """
    db = _get_db_client()
    query = (
        db.collection("workout_logs")
        .where("user_id", "==", user_id)
        .stream()
    )

    logs = []
    for doc in query:
        data = doc.to_dict()
        logs.append(
            f"- {data.get('exercise_name')}: {data.get('sets')} sets x {data.get('reps')} reps "
            f"@ {data.get('weight_lbs')} lbs ({data.get('timestamp')})"
        )

    if not logs:
        return f"No workout history found for user '{user_id}'."

    return f"Workout History for '{user_id}':\n" + "\n".join(logs)


def calculate_fitness_metrics(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str = "male",
    activity_level: str = "moderate",
) -> str:
    """Calculates key fitness metrics including BMI, BMR, TDEE, and Target Heart Rate Zones.

    Args:
        weight_kg: Weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: Gender ('male' or 'female').
        activity_level: Activity level ('sedentary', 'light', 'moderate', 'active', 'very_active').

    Returns:
        A structured summary of calculated BMI, BMR, TDEE, and cardio heart rate zones.
    """
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2) if height_m > 0 else 0.0

    # Mifflin-St Jeor Equation
    if gender.lower() == "female":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    mult = multipliers.get(activity_level.lower(), 1.55)
    tdee = bmr * mult

    max_hr = 220 - age
    fat_burn_low, fat_burn_high = int(max_hr * 0.6), int(max_hr * 0.7)
    cardio_low, cardio_high = int(max_hr * 0.7), int(max_hr * 0.85)

    return (
        f"Fitness Metrics Summary:\n"
        f"- BMI: {bmi:.1f}\n"
        f"- BMR: {int(bmr)} kcal/day\n"
        f"- TDEE: {int(tdee)} kcal/day ({activity_level} activity)\n"
        f"- Target Heart Rate Zones:\n"
        f"  * Fat Burn Zone (60-70%): {fat_burn_low}-{fat_burn_high} bpm\n"
        f"  * Cardio Zone (70-85%): {cardio_low}-{cardio_high} bpm"
    )


def lookup_food_nutrition_facts(query: str) -> str:
    """Fetches real nutritional data (calories, protein, carbs, fats per 100g) for a food item from the Open Food Facts public API.

    Args:
        query: Food item or ingredient name to search (e.g., 'whey protein', 'banana', 'chicken breast', 'oats').

    Returns:
        A formatted summary of matching food products and their nutritional content per 100g.
    """
    import os
    import json
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("NUTRITION_API_KEY", "")

    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={urllib.parse.quote(query)}&search_simple=1&action=process&json=1"
    headers = {"User-Agent": "FitPulseAICoach/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        products = data.get("products", [])
        if not products:
            return f"No food nutrition data found for '{query}'."

        results = []
        for p in products[:3]:
            name = p.get("product_name") or p.get("product_name_en") or "Unknown Product"
            brand = p.get("brands") or "Generic"
            nutriments = p.get("nutriments", {})

            kcal = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal") or "N/A"
            protein = nutriments.get("proteins_100g") or "N/A"
            carbs = nutriments.get("carbohydrates_100g") or "N/A"
            fat = nutriments.get("fat_100g") or "N/A"

            results.append(
                f"- **{name}** ({brand})\n"
                f"  Per 100g: {kcal} kcal | Protein: {protein}g | Carbs: {carbs}g | Fat: {fat}g"
            )

        return f"Nutritional facts for '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error fetching nutrition facts for '{query}': {str(e)}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        generate_exercise_image,
        generate_exercise_video,
        search_exercise_library,
        log_workout_session,
        get_user_workout_history,
        calculate_fitness_metrics,
        lookup_food_nutrition_facts,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)


app = App(
    root_agent=root_agent,
    name="app",
)







