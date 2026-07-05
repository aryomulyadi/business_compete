from crewai import Task
from agents.writer import writer_agent

writing_task = Task(
    description=(
        "Berdasarkan hasil analisis dari Analyst, buat laporan akhir dalam format "
        "Markdown (.md) dengan struktur berikut:\n\n"
        "# Laporan Analisis Kompetitor — {business_field}\n\n"
        "## 1. Ringkasan Eksekutif\n"
        "## 2. Metodologi\n"
        "## 3. Profil Kompetitor Utama\n"
        "## 4. Perbandingan Fitur & Harga\n"
        "## 5. Analisis SWOT\n"
        "## 6. Strategi Positioning\n"
        "## 7. Market Gap & Rekomendasi\n"
        "## 8. Kesimpulan\n"
        "## 9. Daftar Sumber (URL)\n\n"
        "Tulis dalam Bahasa Indonesia yang profesional, rapi, dan actionable. "
        "Simpan laporan ke file Markdown."
    ),
    expected_output=(
        "File Markdown (.md) berisi laporan analisis kompetitor yang lengkap, "
        "terstruktur, dan siap dipresentasikan. Semua dalam Bahasa Indonesia."
    ),
    agent=writer_agent,
    context=[],  # akan diisi secara otomatis oleh Crew dari task sebelumnya
    output_file="output/laporan_analisis_kompetitor.md",
)
