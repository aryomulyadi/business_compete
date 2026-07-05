from crewai import Task
from agents.analyst import analyst_agent

analysis_task = Task(
    description=(
        "Berdasarkan data mentah dari Researcher, lakukan analisis berikut:\n"
        "1. Buat Analisis SWOT (Strengths, Weaknesses, Opportunities, Threats) "
        "untuk bisnis klien di bidang {business_field}\n"
        "2. Buat tabel perbandingan fitur dan harga antar kompetitor\n"
        "3. Berikan strategi positioning yang membedakan klien dari kompetitor\n"
        "4. Identifikasi celah pasar (market gap) yang bisa dimanfaatkan\n\n"
        "Gunakan data yang sudah dikumpulkan, jangan berasumsi tanpa data."
    ),
    expected_output=(
        "Dokumen analisis yang mencakup SWOT matrix, tabel perbandingan kompetitor, "
        "strategi positioning, dan market gap. Semua dalam Bahasa Indonesia."
    ),
    agent=analyst_agent,
    context=[],  # akan diisi secara otomatis oleh Crew dari task sebelumnya
)
