import os
import sys
import io
from dotenv import load_dotenv
from crewai import Crew, Process

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from agents.researcher import researcher_agent
from agents.analyst import analyst_agent
from agents.writer import writer_agent
from tasks.research_task import research_task
from tasks.analysis_task import analysis_task
from tasks.writing_task import writing_task

load_dotenv()

os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

business_field = input("Masukkan bidang bisnis yang ingin dianalisis (contoh: 'E-commerce Fesyen'): ")

research_task.description = research_task.description.replace("{business_field}", business_field)
analysis_task.description = analysis_task.description.replace("{business_field}", business_field)
writing_task.description = writing_task.description.replace("{business_field}", business_field)

research_task.expected_output = research_task.expected_output.replace("{business_field}", business_field)
analysis_task.expected_output = analysis_task.expected_output.replace("{business_field}", business_field)
writing_task.expected_output = writing_task.expected_output.replace("{business_field}", business_field)

analysis_task.context = [research_task]
writing_task.context = [analysis_task]

crew = Crew(
    agents=[researcher_agent, analyst_agent, writer_agent],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

print("\n" + "=" * 60)
print("✅ LAPORAN TELAH BERHASIL DIBUAT!")
print("=" * 60)
print(f"📄 File: output/laporan_analisis_kompetitor.md")
print("=" * 60)
