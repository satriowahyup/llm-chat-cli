from google.genai import errors

from .client import ChatSession
from .config import DEFAULT_SYSTEM_PROMPT, load_settings

HELP_TEXT = """Perintah:
  /help           tampilkan bantuan
  /reset          hapus riwayat percakapan
  /system <teks>  ganti persona AI (riwayat direset)
  /tokens         lihat total token yang terpakai
  /exit           keluar
"""


def main() -> None:
    try:
        settings = load_settings()
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    session = ChatSession(settings, DEFAULT_SYSTEM_PROMPT)
    print(f"llm-chat-cli | model: {settings.model}")
    print("Ketik /help untuk bantuan.\n")

    while True:
        try:
            user_input = input("Kamu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            command, _, arg = user_input.partition(" ")
            if command in {"/exit", "/quit"}:
                print("Sampai jumpa!")
                break
            elif command == "/help":
                print(HELP_TEXT)
            elif command == "/reset":
                session.reset()
                print("Riwayat dihapus.\n")
            elif command == "/system":
                if arg:
                    session.set_system_prompt(arg)
                    print("Persona diganti, riwayat direset.\n")
                else:
                    print("Contoh: /system Kamu adalah guru Python yang sabar\n")
            elif command == "/tokens":
                print(f"Total token terpakai: {session.total_tokens}\n")
            else:
                print("Perintah tidak dikenal. Ketik /help.\n")
            continue

        print("AI: ", end="", flush=True)
        try:
            for text in session.send(user_input):
                print(text, end="", flush=True)
            print("\n")
        except errors.APIError as e:
            print(f"\n[Error {e.code}] {e.message}\n")