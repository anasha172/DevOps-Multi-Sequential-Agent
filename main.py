from crewai import Crew, Process

from agents import issue_investigator, log_analyzer, solution_specialist
from tasks import analyze_logs_task, investigate_issue_task, provide_solution_task

devops_crew = Crew(
    agents=[log_analyzer, issue_investigator, solution_specialist],
    tasks=[analyze_logs_task, investigate_issue_task, provide_solution_task],
    verbose=True,
    process=Process.sequential,
)

if __name__ == "__main__":
    print("=" * 60)
    print("DevOps Issue Analysis v2")
    print("Features: Structured Output | Guardrails")
    print("=" * 60)

    print("\nScenario 1: Kubernetes Deployment Analysis")
    print("-" * 40)
    result = devops_crew.kickoff(
        inputs={"log_file_path": "../../dummy_logs/kubernetes_deployment_error.log"}
    )

    print("\nAnalysis completed!")
