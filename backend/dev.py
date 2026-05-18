"""Windows-safe development entry point.

Run with `py dev.py` from the backend/ directory.
Do NOT use `py -m uvicorn main:app --reload` on Windows — it forces an event
loop that breaks Playwright. loop="none" leaves the loop to the app/default.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="none",
        reload_dirs=["."],
    )
