from crewai import Task
from agents.researcher import researcher_agent

research_task = Task(
    description=(
        "Cari informasi mendalam tentang kompetitor bisnis di bidang {business_field}. "
        "Kumpulkan data berikut sebanyak mungkin:\n"
        "1. Daftar kompetitor utama beserta harga produk/layanan mereka\n"
        "2. Fitur-fitur unggulan yang ditawarkan setiap kompetitor\n"
        "3. Review negatif atau kelemahan yang sering dikeluhkan pelanggan\n"
        "4. Strategi pemasaran yang mereka gunakan\n\n"
        "Gunakan SerperDevTool untuk mencari di internet. Catat URL sumber setiap informasi."
    ),
    expected_output=(
        "Dokumen teks terstruktur berisi data mentah kompetitor: daftar kompetitor, "
        "harga, fitur, review negatif, dan sumber URL. Semua dalam Bahasa Indonesia."
    ),
    agent=researcher_agent,
)
