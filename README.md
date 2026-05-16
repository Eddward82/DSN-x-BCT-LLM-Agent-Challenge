# DSN x BCT LLM Agent Challenge
**Team:** Solo | **Dataset:** Yelp | **LLM:** Claude (Anthropic)

---

## What This Does

| Task | Endpoint | Description |
|------|----------|-------------|
| Task A — User Modeling | `POST /task-a/simulate-review` | Simulates how a user would rate & review a business they haven't visited |
| Task B — Recommendation | `POST /task-b/recommend` | Returns a personalised ranked list of businesses for a user |

---

## Setup (3 Steps)

### 1. Clone & enter the project
```bash
git clone <your-repo-url>
cd yelp-agent
```

### 2. Add your API key
```bash
cp .env.example .env
# Open .env and replace with your real Anthropic API key
```

### 3. Run with Docker
```bash
docker build -t yelp-agent .
docker run -p 8000:8000 --env-file .env yelp-agent
```

The server will be live at: **http://localhost:8000**

---

## Test the Endpoints

Once the server is running, open **http://localhost:8000/docs** in your browser.
You'll see an interactive UI where you can test both tasks directly.

Or use the terminal:

**Test Task A:**
```bash
curl -X POST http://localhost:8000/task-a/simulate-review \
  -H "Content-Type: application/json" \
  -d @tests/task_a_sample.json
```

**Test Task B:**
```bash
curl -X POST http://localhost:8000/task-b/recommend \
  -H "Content-Type: application/json" \
  -d @tests/task_b_sample.json
```

---

## Project Structure

```
yelp-agent/
├── app/
│   └── main.py          # All API logic — Task A + Task B
├── tests/
│   ├── task_a_sample.json   # Sample input for Task A
│   └── task_b_sample.json   # Sample input for Task B
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## How It Works

### Task A — User Modeling
1. Takes user's review history (name, city, past ratings + review text)
2. Analyses their tone, rating behaviour, and cultural signals
3. Generates a simulated rating + review in that user's exact voice
4. Contextualised for Nigerian users (Pidgin, local references, etc.)

### Task B — Recommendation
1. Takes user persona + list of available businesses
2. Reasons about the user's preferences, city, and context
3. Returns ranked recommendations with personalised explanations
4. Handles cold-start users and cross-domain scenarios

---

## Dataset
Using the **Yelp Open Dataset**: https://www.yelp.com/dataset
Key files used: `yelp_academic_dataset_review.json`, `yelp_academic_dataset_business.json`
