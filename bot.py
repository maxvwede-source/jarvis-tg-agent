#!/usr/bin/env python3
"""JARVIS Telegram AI agent - long-polling worker designed for GitHub Actions cron.
Stateless-friendly: conversation memory lives in state.json which the workflow commits back."""
import json, os, urllib.request, urllib.error

TG_TOKEN = os.environ["TG_BOT_TOKEN"]
DAHL_KEY = os.environ.get("DAHL_KEY", "")
STATE_FILE = "state.json"
API_TG = f"https://api.telegram.org/bot{TG_TOKEN}"
API_DAHL = "https://inference.dahl.global/v1/chat/completions"
MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
MAX_UPDATES_PER_RUN = 20

SYSTEM_PROMPT = (
    "You are JARVIS, a sharp AI assistant modeled on Tony Stark's AI, running inside a "
    "Telegram bot built by your owner ('the boss'). Personality: concise, witty, brutally "
    "honest, always useful; occasional light sarcasm; address user as 'sir' sparingly. "
    "Answer directly first - detail only when asked. Plain text only (no markdown)."
)

def http(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    })
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

def tg(method, **params):
    try:
        return http(f"{API_TG}/{method}", params)
    except Exception as e:
        print("tg error:", method, str(e)[:120])
        return {"ok": False}

def ask_dahl(history):
    import time as _t
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-11:]
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    last_err = None
    for attempt in range(6):
        try:
            d = http(API_DAHL, payload)
            content = (d.get("choices") or [{}])[0].get("message", {}).get("content")
            if not content:
                raise RuntimeError("empty response: " + json.dumps(d)[:120])
            return content.strip()
        except urllib.error.HTTPError as e:
            body = ""
            try: body = e.read().decode()[:80]
            except Exception: pass
            last_err = f"HTTP {e.code} {body}"
            print(f"dahl attempt {attempt+1} failed: {last_err}")
        except Exception as e:
            last_err = str(e)[:120]
            print(f"dahl attempt {attempt+1} failed: {last_err}")
        _t.sleep(4)
    raise RuntimeError("Dahl down after 6 tries: " + str(last_err))

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"offset": 0, "chats": {}}

def save_state(s):
    json.dump(s, open(STATE_FILE, "w"), indent=1)

def main():
    state = load_state()
    offset = state.get("offset", 0)

    res = tg("getUpdates", offset=offset, timeout=25, limit=MAX_UPDATES_PER_RUN)
    if not res.get("ok"):
        print("getUpdates failed:", json.dumps(res)[:200]); return

    updates = res.get("result", [])
    print(f"fetched {len(updates)} update(s), starting offset {offset}")
    if not updates:
        return

    for u in updates:
        offset = u["update_id"] + 1
        msg = u.get("message") or u.get("edited_message") or {}
        chat_id, text = (msg.get("chat") or {}).get("id"), (msg.get("text") or "").strip()
        if not chat_id or not text:
            continue
        text = text[:3500]
        print(f"msg from {chat_id}: {text[:60]!r}")

        tg("sendChatAction", chat_id=chat_id, action="typing")

        chats = state.setdefault("chats", {})
        hist = chats.setdefault(str(chat_id), [])[-10:]
        try:
            if text.startswith("/start"):
                reply = ("Online, sir. I'm JARVIS - powered by DeepSeek-V4-Flash.\n"
                         "Ask me anything: coding, math, forex calculations, plans, research.")
            else:
                hist.append({"role": "user", "content": text})
                reply = ask_dahl(hist)
                hist.append({"role": "assistant", "content": reply})
                chats[str(chat_id)] = hist[-10:]
        except Exception as e:
            print("dahl error:", str(e)[:200])
            reply = "Backend hiccup, sir - retry in a moment. (" + str(e)[:100] + ")"

        for i in range(0, min(len(reply), 12000), 4000):
            tg("sendMessage", chat_id=chat_id, text=reply[i:i + 4000])

    state["offset"] = offset
    save_state(state)
    print("done, new offset:", offset)

if __name__ == "__main__":
    main()
