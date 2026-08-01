"""
Entry point for running the Website Intelligence Service on Windows.

WHY THIS FILE EXISTS:
  Playwright requires ProactorEventLoop to launch browser subprocesses.
  On Windows, asyncio defaults to SelectorEventLoop which raises
  NotImplementedError when trying to create subprocesses.

WHY reload=False:
  uvicorn's --reload mode spawns a child subprocess for the worker.
  That child process creates its own event loop BEFORE importing app.main,
  so any policy set in app.main is too late.
  Without reload, uvicorn uses asyncio.run() in the same process, which
  respects the WindowsProactorEventLoopPolicy set below.

Usage:
    python run.py
"""

import asyncio
import sys

# MUST be set before uvicorn creates the event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,   # reload=True spawns subprocesses that bypass the policy above
        log_level="info",
    )
