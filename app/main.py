from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import os
import json

app = FastAPI(
    title="DSN x BCT LLM Agent Challenge",
    description="Task A: User Modeling | Task B: Recommendation",
    version="1.0.0"
)

def get_client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

# ─────────────────────────────────────────────
# SHARED MODELS
# ─────────────────────────────────────────────

class Review(BaseModel):
    business_name: str
    category: str          # e.g. "Fast Food", "Chinese Restaurant"
    rating: float
    review_text: str

class UserPersona(BaseModel):
    user_id: str
    name: str
    city: str              # e.g. "Lagos", "Abuja"
    past_reviews: List[Review]

# ─────────────────────────────────────────────
# TASK A — USER MODELING
# ─────────────────────────────────────────────

class TaskARequest(BaseModel):
    user_persona: UserPersona
    target_business: str        # name of the business to review
    target_category: str        # category of the business
    target_description: str     # brief description of the business

class TaskAResponse(BaseModel):
    simulated_rating: float
    simulated_review: str
    reasoning: str

@app.post("/task-a/simulate-review", response_model=TaskAResponse)
async def simulate_review(request: TaskARequest):
    """
    TASK A — User Modeling
    Given a user persona and their past reviews, simulate how they
    would rate and review a new business they haven't visited yet.
    """

    # Build a summary of the user's past behaviour
    past_reviews_text = "\n".join([
        f"- {r.business_name} ({r.category}): {r.rating}/5 stars — \"{r.review_text}\""
        for r in request.user_persona.past_reviews
    ])

    prompt = f"""You are an expert at understanding user behaviour and writing patterns from online reviews.

A user named {request.user_persona.name} from {request.user_persona.city} has the following review history on Yelp:

{past_reviews_text}

Now simulate how this EXACT user would review a new business they haven't visited yet:
- Business: {request.target_business}
- Category: {request.target_category}
- Description: {request.target_description}

Study the user's:
1. Writing style (formal/casual, long/short, Pidgin English or standard?)
2. Rating tendency (are they generous or strict with stars?)
3. What they typically praise or complain about
4. Their cultural context as someone from {request.user_persona.city}

Respond ONLY with a valid JSON object in this exact format:
{{
  "simulated_rating": <number between 1.0 and 5.0>,
  "simulated_review": "<the review text written exactly in this user's voice>",
  "reasoning": "<brief explanation of why you gave this rating and wrote in this style>"
}}"""

    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        return TaskAResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)}\nRaw: {raw}")


# ─────────────────────────────────────────────
# TASK B — RECOMMENDATION
# ─────────────────────────────────────────────

class TaskBRequest(BaseModel):
    user_persona: UserPersona
    available_businesses: List[dict]   # list of businesses to rank
    context: Optional[str] = None      # e.g. "Looking for somewhere to eat after church on Sunday"

class TaskBResponse(BaseModel):
    recommendations: List[dict]        # ranked list with reasons
    agent_reasoning: str

@app.post("/task-b/recommend", response_model=TaskBResponse)
async def recommend(request: TaskBRequest):
    """
    TASK B — Recommendation
    Given a user persona and a list of available businesses,
    return a personalised ranked list of recommendations.
    """

    past_reviews_text = "\n".join([
        f"- {r.business_name} ({r.category}): {r.rating}/5 — \"{r.review_text}\""
        for r in request.user_persona.past_reviews
    ])

    businesses_text = json.dumps(request.available_businesses, indent=2)

    context_line = f"\nUser's current context: {request.context}" if request.context else ""

    prompt = f"""You are a highly intelligent recommendation agent that understands Nigerian user preferences and cultural context.

USER PROFILE:
Name: {request.user_persona.name}
City: {request.user_persona.city}
{context_line}

PAST REVIEW HISTORY:
{past_reviews_text}

AVAILABLE BUSINESSES TO RANK:
{businesses_text}

Your job:
1. Deeply analyse this user's taste, preferences, price sensitivity, and cultural context
2. Consider their city ({request.user_persona.city}) and any contextual signals
3. Rank ALL the available businesses from most to least recommended FOR THIS SPECIFIC USER
4. Give a clear, specific reason for each recommendation that references the user's actual history

Respond ONLY with a valid JSON object:
{{
  "recommendations": [
    {{
      "rank": 1,
      "business_name": "<name>",
      "predicted_rating": <1.0-5.0>,
      "reason": "<specific reason tied to this user's history and context>"
    }}
  ],
  "agent_reasoning": "<overall explanation of your recommendation strategy for this user>"
}}"""

    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        return TaskBResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)}\nRaw: {raw}")


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "running",
        "tasks": {
            "task_a": "/task-a/simulate-review",
            "task_b": "/task-b/recommend",
            "docs": "/docs"
        }
    }
