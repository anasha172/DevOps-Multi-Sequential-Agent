import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from crewai import Agent, Crew, Process, Task
    from crewai.llm import LLM
    from crewai.tasks.task_output import TaskOutput
except Exception as e:
    # crewai might not be installed in every environment
    raise ImportError("crewai library is required to run the pipeline. Install it in your environment.")

from pydantic import BaseModel, Field

LOG_INPUT = os.getenv('LOG_INPUT') or """[2024-01-15 14:32:15.123] INFO: Starting deployment of myapp-deployment\n[2024-01-15 14:32:16.567] WARNING: Pod myapp-deployment-7b8c9d5f4-abc12 in Pending state\n[2024-01-15 14:32:17.890] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 failed to start\n[2024-01-15 14:32:18.123] ERROR: Failed to pull image \"myapp:v1.2.3\": pull access denied, repository does not exist or may require 'docker login'\n[2024-01-15 14:32:18.456] ERROR: Pod myapp-deployment-7b8c9d5f4-abc12 status: ImagePullBackOff\n[2024-01-15 14:32:25.901] ERROR: Deployment rollout failed: deployment \"myapp-deployment\" exceeded its progress deadline\n[2024-01-15 14:32:26.789] WARNING: Service myapp-service has no available endpoints\n[2024-01-15 14:32:29.456] CRITICAL: Production deployment failed - rollback initiated\n"""

OUTPUT_DIR = Path("task_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class LogAnalysisReport(BaseModel):
    primary_issue: str = Field(description="One-line description of the main issue")
    root_cause: str = Field(description="Root cause analysis based on log evidence")
    errors: list[str] = Field(description="All errors found in the log")
    affected_components: list[str] = Field(description="System components affected")
    timeline: list[str] = Field(description="Sequence of events leading to failure")


def _get_llm():
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    if openrouter_key:
        return LLM(model="openai/gpt-4o-mini", api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
    elif groq_key:
        return LLM(model="openai/llama-3.3-70b-versatile", api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    else:
        raise RuntimeError('Set OPENROUTER_API_KEY or GROQ_API_KEY in environment before running the pipeline')


async def _run_async_pipeline(log_input: str = LOG_INPUT):
    llm = _get_llm()

    log_analyzer = Agent(
        role="DevOps Log Analyzer",
        goal="Analyze log files to identify and extract specific issues, errors, and failure patterns",
        llm=llm,
        backstory="""You are a senior DevOps engineer with 10 years of experience in 
    analyzing production logs and identifying critical issues. You excel at parsing 
    through complex log files, identifying error patterns, extracting relevant error 
    messages, and determining the root cause of failures from log data.""",
        verbose=True,
    )

    issue_investigator = Agent(
        role="DevOps Issue Investigator",
        goal="Investigate identified issues by searching documentation, forums, and known solutions online",
        llm=llm,
        backstory="""You are a DevOps troubleshooting specialist who excels at quickly 
    finding solutions to technical problems. You know how to search effectively for 
    similar issues, identify reliable sources, and gather comprehensive information 
    about error patterns and their solutions.""",
        verbose=True,
    )

    solution_specialist = Agent(
        role="DevOps Solution Specialist",
        goal="Provide clear, actionable solutions with step-by-step instructions based on investigation findings",
        llm=llm,
        backstory="""You are a DevOps solutions architect who specializes in creating 
    reliable, step-by-step remediation plans for infrastructure and deployment issues.""",
        verbose=True,
    )

    def validate_log_analysis(result: TaskOutput):
        report = result.pydantic
        if not report or not report.errors:
            return (False, "Must identify at least one error")
        return (True, report)

    analyze_task = Task(
        description="Analyze the following log data to identify issues:\n{log_data}",
        expected_output="A structured log analysis report",
        output_pydantic=LogAnalysisReport,
        guardrail=validate_log_analysis,
        agent=log_analyzer,
        output_file=str(OUTPUT_DIR / 'log_analysis.json'),
    )

    investigate_task = Task(
        description="""Based on the log analysis findings, investigate the identified issue.\n\nYour investigation should:\n1. Identify common causes and scenarios for this type of issue\n2. Find known solutions and best practices\n3. Gather information about proven fixes and workarounds""",
        expected_output="A comprehensive investigation report",
        agent=issue_investigator,
        context=[analyze_task],
        output_file=str(OUTPUT_DIR / 'investigation_report.md'),
    )

    solution_task = Task(
        description="""Based on the log analysis and investigation findings, provide a complete solution.\n\nYour solution should:\n1. Create a step-by-step remediation plan with specific commands\n2. Provide verification steps to confirm the fix\n3. Suggest monitoring and prevention measures""",
        expected_output="A detailed remediation plan with step-by-step commands",
        guardrail="The solution must include at least 3 specific, copy-pasteable shell commands. Reject if it only contains general advice without concrete commands.",
        agent=solution_specialist,
        context=[analyze_task, investigate_task],
        output_file=str(OUTPUT_DIR / 'solution_plan.md'),
    )

    pipeline_crew = Crew(
        agents=[log_analyzer, issue_investigator, solution_specialist],
        tasks=[analyze_task, investigate_task, solution_task],
        process=Process.sequential,
        verbose=True,
    )

    result = await pipeline_crew.kickoff_async(inputs={"log_data": log_input})

    # write structured JSON if available
    outputs = {}
    try:
        j = result.pydantic.model_dump()
        (OUTPUT_DIR / 'log_analysis.json').write_text(json.dumps(j, indent=2), encoding='utf-8')
        outputs['log_analysis'] = j
    except Exception:
        outputs['log_analysis'] = None

    # Investigation and solution outputs are saved by the Task.output_file mechanism; read them if present
    inv_path = OUTPUT_DIR / 'investigation_report.md'
    sol_path = OUTPUT_DIR / 'solution_plan.md'
    outputs['investigation'] = inv_path.read_text(encoding='utf-8') if inv_path.exists() else None
    outputs['solution'] = sol_path.read_text(encoding='utf-8') if sol_path.exists() else None

    outputs['raw'] = result.raw
    return outputs


def run_pipeline(log_input: str = LOG_INPUT):
    """Synchronous wrapper that runs the async pipeline and returns outputs."""
    return asyncio.run(_run_async_pipeline(log_input))
