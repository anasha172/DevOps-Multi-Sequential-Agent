# DevOps-Multi-Sequential-Agent
# Production-Ready CrewAI DevOps Troubleshooting Pipeline

An AI-powered DevOps troubleshooting pipeline built with **CrewAI**.

This project demonstrates how to take a basic multi-agent workflow and make it more reliable for production by adding **structured outputs, validation guardrails, automatic retries, multi-agent context, and a visual Streamlit dashboard**.

The pipeline takes application/deployment logs as input and produces a structured analysis, an investigation report, and a step-by-step remediation plan.

---

## 🚀 What Is This Project?

When a production deployment fails, engineers usually have to go through large amounts of logs to figure out:

* What went wrong?
* What is the root cause?
* Which components are affected?
* What should be fixed?
* How can the issue be prevented from happening again?

This project uses a **CrewAI multi-agent pipeline** to automate that process.

Instead of simply asking one AI agent to read a log and generate an answer, the project introduces production-oriented controls to make the AI workflow more reliable.

### The pipeline

```text
Deployment / Application Logs
            │
            ▼
   ┌─────────────────────┐
   │   Log Analyzer      │
   │                     │
   │ Finds errors,       │
   │ root causes,        │
   │ affected components │
   │ and timeline        │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  Guardrail /         │
   │  Validation          │
   │                      │
   │ Checks whether the   │
   │ analysis is useful   │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Issue Investigator  │
   │                     │
   │ Investigates causes │
   │ and best practices  │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Solution Specialist │
   │                     │
   │ Creates a concrete  │
   │ remediation plan    │
   └──────────┬──────────┘
              │
              ▼
      ┌─────────────────┐
      │ Generated       │
      │ Outputs         │
      ├─────────────────┤
      │ log_analysis    │
      │ investigation   │
      │ solution_plan   │
      └────────┬────────┘
               │
               ▼
      Streamlit Dashboard
```

The three agents run sequentially, with later tasks receiving the output/context from earlier tasks.

---

# ✨ What Makes This "Production-Ready"?

The main purpose of this notebook is not simply demonstrating agents.

It demonstrates how to make an AI workflow **more reliable and controllable**.

The project addresses three major problems.

## 1. Structured Output

### The problem

LLMs normally return free-form text.

That makes it difficult for another part of your application to reliably access things such as:

* root cause
* errors
* affected components
* timeline

The notebook demonstrates how parsing raw Markdown/text can become fragile if the model changes its formatting.

### The solution

The project uses a Pydantic model:

```python
class LogAnalysisReport(BaseModel):
    primary_issue: str
    root_cause: str
    errors: list[str]
    affected_components: list[str]
    timeline: list[str]
```

CrewAI's `output_pydantic` is then used to force the agent's response into this structure.

This means the result can be accessed programmatically:

```python
report.primary_issue
report.root_cause
report.errors
report.affected_components
report.timeline
```

rather than trying to parse unpredictable AI-generated text.

---

# 🛡️ 2. Code Guardrails

Structured output guarantees the **shape** of the response, but it doesn't guarantee that the response is actually useful.

For example, the notebook intentionally provides logs containing:

* `0 records processed`
* `Disk usage at 94%`

Even though the messages are labelled `INFO`, they may still represent important operational issues.

Without validation, an agent could return an empty error list and the workflow would continue with a bad analysis.

The project therefore adds a Python guardrail:

```python
def validate_log_analysis(result):
    report = result.pydantic

    if not report or not report.errors:
        return (False, "Must identify at least one error")

    return (True, report)
```

If the output fails validation, the task is rejected and the agent gets another attempt. The notebook demonstrates this behaviour with the guardrail failing on the first attempt and succeeding on the second.

---

# 🤖 3. No-Code Guardrails

Not every validation rule needs a Python function.

For simpler requirements, the project demonstrates using a **plain-English guardrail**.

For example, the final solution task requires:

> At least 3 specific, copy-pasteable shell commands.

If the AI produces only general advice, the output is rejected.

This allows validation rules to be expressed directly in natural language instead of writing custom validation logic for every task.

---

# 🔄 Multi-Agent Pipeline

The final pipeline contains three specialized agents.

### 1. DevOps Log Analyzer

Responsible for analyzing the incoming logs and identifying:

* primary issue
* root cause
* errors
* affected components
* timeline

Its output is validated using both structured output and a code guardrail.

### 2. Issue Investigator

Receives the log analysis and investigates:

* common causes
* possible scenarios
* known solutions
* best practices
* recommended fixes
* workarounds

Its output is saved as:

```text
task_outputs/investigation_report.md
```

### 3. DevOps Solution Specialist

Uses both the original analysis and investigation to create a practical remediation plan.

The task is specifically designed to produce:

* step-by-step fixes
* concrete commands
* verification steps
* monitoring/prevention recommendations

Its output is saved as:

```text
task_outputs/solution_plan.md
```

---

# 📁 Generated Outputs

After running the pipeline, the project creates a `task_outputs/` directory containing:

```text
task_outputs/
├── log_analysis.json
├── investigation_report.md
└── solution_plan.md
```

### `log_analysis.json`

Contains the structured Pydantic analysis:

```json
{
  "primary_issue": "...",
  "root_cause": "...",
  "errors": [],
  "affected_components": [],
  "timeline": []
}
```

The notebook explicitly configures the first task to save its structured result to this file.

### `investigation_report.md`

Contains the investigation into the identified problem, including causes, solutions, best practices, fixes, and workarounds.

### `solution_plan.md`

Contains the final remediation plan, including concrete commands and verification/prevention steps.

---

# 📊 Streamlit Dashboard

The notebook also generates a Streamlit dashboard.

The dashboard provides two main areas:

### Pipeline Flow

Displays the workflow:

```text
Analyze → Investigate → Solution
```

### Outputs

Displays:

* structured log analysis
* investigation report
* solution plan

The dashboard reads the files from `task_outputs/` and displays them in the interface.

By default, the notebook attempts to launch Streamlit on:

```text
http://localhost:8501
```

---

# 🧪 Example Scenario

The notebook uses a simulated Kubernetes deployment failure.

The example contains an application image:

```text
myapp:v1.2.3
```

The deployment encounters:

```text
ImagePullBackOff
```

because the container image cannot be pulled.

The AI pipeline identifies the image-pull problem, investigates possible causes such as registry credentials, and generates a remediation plan involving Kubernetes image-pull secrets and deployment configuration.

The example ultimately demonstrates how the pipeline can move from:

```text
Raw Logs
   ↓
Problem Identification
   ↓
Root Cause Analysis
   ↓
Investigation
   ↓
Remediation
   ↓
Verification
   ↓
Monitoring / Prevention
```

---

# 🛠️ Tech Stack

* **Python**
* **CrewAI**
* **Pydantic**
* **OpenRouter**
* **GPT-4o-mini**
* **Streamlit**
* **python-dotenv**

The notebook configures `gpt-4o-mini` through OpenRouter and loads the API key from an environment variable.

---

# ⚙️ Setup

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

## 3. Install dependencies

Install the packages required by the notebook:

```bash
pip install crewai pydantic python-dotenv streamlit
```

You may also want to install Jupyter if you intend to run the notebook locally:

```bash
pip install jupyter
```

---

# 🔑 Environment Variables

The project expects an OpenRouter API key.

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
```

**Do not commit your `.env` file to GitHub.**

Add this to `.gitignore`:

```text
.env
.venv/
__pycache__/
task_outputs/
```

---

# ▶️ Running the Project

Open the notebook:

```text
02_production_features.ipynb
```

Then run the cells sequentially.

The notebook creates the CrewAI agents and tasks, runs the sequential pipeline, writes the generated outputs to `task_outputs/`, and sets up the Streamlit dashboard.

Once the dashboard is running, open:

```text
http://localhost:8501
```

---

# ⚠️ Important: This Is a Demonstration Project

This repository demonstrates an **AI-powered DevOps troubleshooting workflow**.

The Kubernetes logs and deployment scenarios used in the notebook are example/simulated data.

The generated remediation commands should therefore be treated as **recommendations**, not commands that should automatically be executed against a real production cluster.

Always verify:

* the affected cluster
* namespace
* deployment name
* container image
* registry
* credentials
* generated commands

before applying changes to a real environment.

---

# 🧠 What You Will Learn

By running this project, you can see how to build more reliable agentic workflows using CrewAI.

The main concepts demonstrated are:

### Structured AI outputs

Turn unpredictable LLM responses into typed Python objects.

### Code-based validation

Reject outputs that don't meet programmatic requirements.

### LLM-based validation

Use natural-language requirements for simpler output checks.

### Automatic retries

Give agents another attempt when their output fails validation.

### Agent specialization

Use different agents for analysis, investigation, and solution generation.

### Context passing

Feed the output of one task into subsequent tasks.

### Persistent task outputs

Save AI results as JSON and Markdown files.

### AI workflow visualization

Expose the pipeline and its outputs through a Streamlit dashboard.

The notebook's final recap specifically contrasts raw text with typed outputs, unchecked output with guardrailed retries, and isolated features with the combined multi-agent pipeline.

---

# 🗺️ Project Flow

```text
                  ┌──────────────────┐
                  │   Deployment     │
                  │      Logs        │
                  └────────┬─────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Log Analyzer      │
                │                     │
                │ Structured Output   │
                │ + Code Guardrail    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Issue Investigator  │
                │                     │
                │ Causes + Solutions  │
                │ + Best Practices    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Solution Specialist │
                │                     │
                │ Remediation Plan    │
                │ + No-Code Guardrail │
                └──────────┬──────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │    Outputs       │
                 ├──────────────────┤
                 │ JSON Analysis    │
                 │ Investigation    │
                 │ Solution Plan    │
                 └────────┬─────────┘


# 📌 Project Status

**Status:** Educational / Prototype

This repository currently demonstrates the architecture and behaviour of a production-oriented CrewAI troubleshooting workflow rather than providing a fully deployed autonomous production incident-response system.

---





