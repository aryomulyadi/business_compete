# BizComp AI

Navigasi Arah Bisnis, Kuasai Peta Persaingan.

Platform analisis kompetitor bisnis berbasis AI — SWOT, Five Forces, PESTEL, dan strategi brand dalam satu laporan otomatis. Menggunakan [CrewAI](https://github.com/joaomdmoura/crewAI) dengan tiga agent yang bekerja secara sekuensial: Researcher → Analyst → Writer.

## Fitur

- **Pencarian mendalam** — parallel search dengan 5 query template per bidang bisnis
- **Analisis strategis** — SWOT, Porter's Five Forces, PESTEL, perbandingan kompetitor, gap analysis
- **Ekspor laporan** — Markdown, HTML, PDF
- **Dual interface** — CLI (terminal) & Web UI (Next.js)
- **Validasi URL** — otomatis menghapus URL palsu/halusinasi dari laporan
- **Retry & fallback** — exponential backoff + fallback model jika LLM utama gagal
- **Progress tracking** — real-time progress bar (CLI: Rich, Web: WebSocket)

## Prasyarat

- Python 3.10 – 3.13
- API keys (minimal satu LLM provider + Serper.dev untuk search)

## Setup

```bash
# 1. Clone repo
git clone https://github.com/aryomulyadi/business_compete.git
cd business_compete

# 2. Buat virtual environment
python -m venv .venv

# 3. Aktifkan venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -e .

# 5. Copy & isi environment variables
cp .env.example .env
# Edit .env dengan API key kamu
```

## Konfigurasi

Isi file `.env`:

| Variable | Wajib | Default | Deskripsi |
|---|---|---|---|
| `GROQ_API_KEY` | Ya | - | Groq LLM API key |
| `SERPER_API_KEY` | Ya | - | Serper.dev Google Search API |
| `DEEPSEEK_API_KEY` | Opsional | - | DeepSeek LLM API key |
| `GEMINI_API_KEY` | Opsional | - | Gemini LLM API key |
| `MIMO_API_KEY` | Opsional | - | Mimo LLM API key |
| `MIMO_BASE_URL` | Opsional | `https://api.xiaomimimo.com/v1` | Mimo OpenAI-compatible base URL. Untuk Token Plan gunakan base URL khusus dari Mimo |
| `MIMO_THINKING` | Opsional | `disabled` | Mode thinking Mimo: `disabled` agar output langsung ada di `message.content`, atau `enabled` jika caller menyimpan `reasoning_content` |
| `OMNIROUTE_API_KEY` | Opsional | - | OmniRoute dashboard API key |
| `OMNIROUTE_BASE_URL` | Wajib jika `LLM_PROVIDER=omniroute` | - | OmniRoute OpenAI-compatible base URL, contoh `http://localhost:<port>/v1` |
| `OMNIROUTE_MODEL` | Opsional | `auto` | Model atau combo OmniRoute |
| `LLM_PROVIDER` | Tidak | `mimo` | Provider: `mimo`, `groq`, `deepseek`, `gemini`, `openai`, `openai-mini`, `omniroute` |

## Cara Menjalankan

### CLI

```bash
run_crew
```

Atau:

```bash
python -m deep_research_team.main
```

Kemudian masukkan bidang bisnis yang ingin dianalisis.

### Web UI (Next.js)

```bash
cd frontend
npm run dev
```

Buka http://localhost:3000 di browser.

### Output

Laporan akan tersimpan di folder `output/`:
| File | Format |
|---|---|
| `output/laporan_analisis_kompetitor.md` | Markdown |
| `output/laporan_analisis_kompetitor.html` | HTML |
| `output/laporan_analisis_kompetitor.pdf` | PDF (jika font tersedia) |

## Arsitektur

```
src/deep_research_team/
├── __init__.py
├── settings.py           # Konfigurasi sentral
├── crew.py               # Definisi agent, task, crew
├── main.py               # CLI entry point
├── config/
│   ├── agents.yaml       # Role, goal, backstory agent
│   └── tasks.yaml        # Deskripsi & expected output task
└── tools/
    ├── llm_utils.py      # LLM abstraction, retry, fallback
    ├── search_tool.py    # Serper search, URL validation, cache
    ├── export_utils.py   # Markdown → HTML/PDF converter
    └── progress.py       # Rich-based progress display
```

### Agent Pipeline

```
Researcher ──→ Analyst ──→ Writer
(search data)   (analisis)   (laporan)
```

### Agent

| Agent | Tool | Max Tokens |
|---|---|---|
| **Researcher** | search, scrape, deep search | 4096 |
| **Analyst** | - | 8192 |
| **Writer** | - | 16384 |

### LLM Providers

Provider dapat diganti via env `LLM_PROVIDER`:

| Provider | Model | Catatan |
|---|---|---|
| `mimo` (default) | `mimo-v2.5-pro` via MimoDirect | OpenAI-compatible API Xiaomi Mimo, memakai `max_completion_tokens` dan `thinking=disabled` by default |
| `groq` | `llama-3.3-70b-versatile` | Cepat, rate limit 6k TPM → auto retry |
| `deepseek` | `deepseek-chat` | Stabil, murah |
| `gemini` | `gemini-2.5-flash` | Gratis quota besar |
| `openai` | `gpt-4o` | Bayar |
| `openai-mini` | `gpt-4o-mini` | Murah |
| `omniroute` | `auto` via `OMNIROUTE_BASE_URL` | OpenAI-compatible gateway; fallback internal app dimatikan agar routing ditangani OmniRoute |

### Fallback Mechanism

```
Mimo API retryable error
  → ValueError / provider exception
  → RetryableLLM catch
  → exponential backoff (2s, 4s, 8s)
  → switch ke fallback (groq/llama-3.1-8b-instant)

Groq rate limit
  → RateLimitError raise
  → RetryableLLM catch (isinstance)
  → exponential backoff
  → retry dengan delay semakin besar
```

### URL Pipeline

```
Serper API → cache (MD5 hash) → validate HEAD → filter_fake_urls()
                                                      ↓
                                           ┌─ unreachable → dihapus
                                           └─ domain-root → flagged "terlalu umum"

## Struktur Direktori

```
├── frontend/               # Next.js web UI
├── fastapi_backend/         # FastAPI REST API
├── pyproject.toml          # Build & dependency config
├── .env                    # API keys (jangan di-commit)
├── .env.example            # Template environment
├── .gitignore
├── README.md
├── src/deep_research_team/ # Kode utama
└── output/                 # Laporan & cache (auto-generate)
```

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `SERPER_API_KEY tidak ditemukan` | Pastikan `.env` ada dan variable terisi |
| PDF gagal | Gunakan output HTML → browser → print-to-PDF |
| LLM error | Cek API key, atau ganti `LLM_PROVIDER` |
| Encoding error (Windows) | Sudah di-handle otomatis via UTF-8 wrapper |
