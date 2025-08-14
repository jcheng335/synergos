from synergos.agents.agent_registry import AgentRegistry
from synergos.agents.agent_base import AgentBase
from synergos.agents.resume_agent import ResumeAnalysisAgent
from synergos.agents.job_agent import JobAnalysisAgent
from synergos.agents.interview_agent import InterviewAgent
from synergos.agents.evaluation_agent import EvaluationAgent
from synergos.agents.scheduling_agent import SchedulingAgent
from synergos.agents.email_agent import EmailAgent
from synergos.agents.orchestrator import AgentOrchestrator
from synergos.agents.question_generator_agent import QuestionGeneratorAgent

# Create a global agent registry
agent_registry = AgentRegistry()

# Register all agent types
agent_registry.register("resume", ResumeAnalysisAgent)
agent_registry.register("job", JobAnalysisAgent)
agent_registry.register("interview", InterviewAgent)
agent_registry.register("evaluation", EvaluationAgent)
agent_registry.register("scheduling", SchedulingAgent)
agent_registry.register("email", EmailAgent)
agent_registry.register("question_generator", QuestionGeneratorAgent)

# Create the orchestrator
orchestrator = AgentOrchestrator(agent_registry) 