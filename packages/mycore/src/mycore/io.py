import sys
import json

IS_BROWSER = hasattr(sys, "implementation") and sys.implementation.name in ("brython", "transcrypt")

if IS_BROWSER:
    from browser import window

    async def load_file(path):
        res = await window.fetch(path)
        return await res.text()

    async def load_json(path):
        text = await load_file(path)
        return json.loads(text)
else:
    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def load_json(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
