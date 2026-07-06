from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from deep_research_team.settings import (
    AGENTS_CONFIG,
    ANALYST_MAX_ITER,
    ANALYST_MAX_TOKENS,
    REPORT_FILE,
    RESEARCHER_MAX_ITER,
    RESEARCHER_MAX_TOKENS,
    TASKS_CONFIG,
    WRITER_MAX_TOKENS,
    setup_logging,
)
from deep_research_team.tools.llm_utils import get_llm
from deep_research_team.tools.search_tool import (
    deep_search,
    scrape_website,
    search_internet,
)
from deep_research_team.tools.progress import progress_step_handler

logger = setup_logging(__name__)


@CrewBase
class DeepResearchCrew:
    """Deep Research Team crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = AGENTS_CONFIG
    tasks_config = TASKS_CONFIG

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=get_llm(max_tokens=RESEARCHER_MAX_TOKENS),
            tools=[search_internet, scrape_website, deep_search],
            verbose=True,
            max_iter=RESEARCHER_MAX_ITER,
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],
            llm=get_llm(max_tokens=ANALYST_MAX_TOKENS),
            verbose=True,
            max_iter=ANALYST_MAX_ITER,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=get_llm(max_tokens=WRITER_MAX_TOKENS),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],
            context=[self.research_task()],
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],
            context=[self.analysis_task()],
            output_file=str(REPORT_FILE),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            step_callback=progress_step_handler,
        )
