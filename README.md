# llm-chat-cli

Terminal chatbot dengan streaming dan memori multi-turn, dibangun dengan Python dan Gemini API.

## Fitur
- Percakapan multi-turn
- Streaming respons
- Persona yang bisa diganti (`/system`)
- Retry otomatis dengan exponential backoff
- Pelacakan penggunaan token

## Instalasi
```bash
git clone https://github.com/<username>/llm-chat-cli.git
cd llm-chat-cli
uv sync
cp .env.example .env   # lalu isi GEMINI_API_KEY
```

## Menjalankan
Jalankan dari folder proyek setelah mengisi file `.env` dengan `GEMINI_API_KEY`:

```powershell
uv run llm-chat-cli
```

Jika Windows Security atau kebijakan keamanan Windows memblokir perintah `llm-chat-cli`, dan Anda sudah memastikan proyek ini tepercaya, coba jalankan entry point secara langsung:

```powershell
uv run python -c "from llm_chat_cli import main; main()"
```

Jangan menonaktifkan Windows Security untuk menjalankan aplikasi. Jika pemblokiran tetap terjadi, periksa detail peringatannya atau minta bantuan administrator perangkat.

## Perintah
`/help`, `/reset`, `/system <teks>`, `/tokens`, `/exit`

## Testing
```bash
uv run pytest
```

## Struktur
- `config.py`: pengaturan dan environment
- `client.py`: logika LLM (streaming, retry)
- `cli.py`: antarmuka terminal

## Roadmap
- [ ] Endpoint FastAPI
- [ ] Structured output
- [ ] Dukungan provider lain
