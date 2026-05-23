"""Production entry point.

Run with `python start.py`. Binds to 0.0.0.0 and reads PORT from the
environment (Render/Railway/etc.), defaulting to 10000. loop="none" leaves the
event loop to the app/default so Playwright works.
"""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, loop="none")
