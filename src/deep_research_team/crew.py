from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from deep_research_team.tools.llm_utils import get_llm
from deep_research_team.tools.search_tool import (
    deep_search,
    scrape_website,
    search_internet,
)
from deep_research_team.tools.progress import progress_step_handler


@CrewBase
class DeepResearchCrew:
    """Deep Research Team crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            llm=get_llm(max_tokens=4096),
            tools=[search_internet, scrape_website, deep_search],
            verbose=True,
            max_iter=8,
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],  # type: ignore[index]
            llm=get_llm(max_tokens=8192),
            verbose=True,
            max_iter=3,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],  # type: ignore[index]
            llm=get_llm(max_tokens=16384),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],  # type: ignore[index]
            context=[self.research_task()],
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],  # type: ignore[index]
            context=[self.analysis_task()],
            output_file="output/laporan_analisis_kompetitor.md",
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Deep Research Team crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            step_callback=progress_step_handler,
        )
