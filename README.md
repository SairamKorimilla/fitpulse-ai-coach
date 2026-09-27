# ⚡ FitPulse AI Coach

An intelligent AI fitness and nutrition coach powered by Google Cloud, Vertex AI, and Google ADK (Agent Development Kit). FitPulse AI Coach provides personalized workout recommendations, interactive exercise tracking cards, AI exercise image and video generation, health metric calculations, and real-time nutrition lookups.

![FitPulse AI Coach Demo](demo.gif)

---

## 🌟 Key Features & Capabilities

FitPulse AI Coach implements the following tools and integrations:

### 🏋️‍♂️ Personalized Fitness & Workout Coaching
- **Interactive A2UI Cards**: Renders structured workout plans into interactive A2UI surface cards complete with checkable sets, exercise details, and target muscle groups.
- **Firestore Exercise Library Search**: Queries a Google Cloud Firestore collection of targeted exercises (`search_exercise_library`) by muscle group, equipment, or exercise name.
- **Workout Logging & History**: Records completed workout sessions directly to Firestore (`log_workout_session`) and retrieves user history (`get_user_workout_history`).

### 🎨 Multimodal AI Asset Generation
- **Exercise Image Generation**: Generates visual exercise illustrations on-demand (`generate_exercise_image`) using Vertex AI's `imagen-3.0-generate-002` model and uploads them to Cloud Storage.
- **Exercise Video Generation**: Generates short exercise demonstration videos (`generate_exercise_video`) using Vertex AI's `gemini-omni-flash-preview` Omni model in the global region. Saves videos to ADK Artifacts panel and uploads to Google Cloud Storage.

### 📊 Health Metrics & Nutrition Lookups
- **Fitness Calculators**: Calculates Body Mass Index (BMI), Basal Metabolic Rate (BMR), and Total Daily Energy Expenditure (TDEE) based on user height, weight, age, and activity level (`calculate_fitness_metrics`).
- **Nutrition Facts Lookup**: Fetches real-time calorie and macronutrient breakdowns (protein, carbs, fat) for foods via Open Food Facts API (`lookup_food_nutrition_facts`).

### 🧠 Persistent Long-Term Memory
- **Agent Memory Bank**: Automatically extracts key fitness preferences, health metrics, and workout goals during conversations and persists them across user sessions using ADK Memory Bank (`PreloadMemoryTool` and `generate_memories_callback`).

---

## 🛠️ Google Cloud Services & Architecture

| Component | Technology / Service | Purpose |
|---|---|---|
| **Agent Framework** | Google ADK (Agent Development Kit) | Core agent orchestration, tool routing, and memory handling |
| **LLM Engine** | Vertex AI Gemini (`gemini-2.5-flash`) | Natural language understanding and reasoning |
| **Omni Model** | Vertex AI (`gemini-omni-flash-preview`) | Multi-modal video generation |
| **Image Model** | Vertex AI Imagen (`imagen-3.0-generate-002`) | Exercise illustration generation |
| **Database** | Google Cloud Firestore | NoSQL document storage for exercise library and workout logs |
| **Asset Storage** | Google Cloud Storage (GCS) | Public HTTPS hosting for generated exercise images and videos |
| **Deployment Target** | Vertex AI Agent Runtime | Scalable serverless agent hosting |
| **Frontend UI** | FastAPI + Vanilla JS + HTML5 + CSS3 | Interactive Web UI with dark mode, markdown rendering, and A2UI cards |

---

## 📋 Roadmap & Planned Features

The following items were defined in preliminary design briefs but are not yet implemented in the current codebase:
- [ ] **Live Wearable Sensor Integration**: *Planned, not yet implemented* (Streaming real-time heart rate and wearable telemetry).
- [ ] **AI Form Correction via Camera**: *Planned, not yet implemented* (Pose estimation and video analysis of user exercise form).

---

## 🚀 Setup & Local Development Instructions

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated to your GCP project
- Google Cloud project with Firestore, Vertex AI API, and Cloud Storage enabled

### 1. Environment Setup

Clone the repository and install Python dependencies:

```bash
git clone https://github.com/your-username/fitpulse-ai-coach.git
cd fitpulse-ai-coach

python3 -m venv .venv
source .venv/bin/activate
pip install -r pyproject.toml
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_GENAI_USE_VERTEXAI=true
```

### 3. Seed Database (Firestore)

Populate the Firestore database with sample exercise library items:

```bash
python seed_database.py
```

### 4. Run the Application Locally

Start the FastAPI frontend server locally:

```bash
python -m frontend.main
```

Open your browser and navigate to `http://localhost:8080` to interact with FitPulse AI Coach locally.

---

## 🚢 Deployment Instructions

To deploy the agent to Google Cloud Agent Runtime:

```bash
agents-cli deploy --project your-gcp-project-id --region us-east1
```

To deploy the web frontend to Cloud Run:

```bash
gcloud run deploy fitpulse-ai-coach-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated
```
