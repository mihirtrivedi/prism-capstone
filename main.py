"""Entrypoint to launch the Prism LLM Gateway.
Usage:
    python main.py [--port 8080] [--host 0.0.0.0]
"""

import argparse
import sys
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Prism LLM Gateway Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    print(f"Starting Prism LLM Gateway on http://{args.host}:{args.port} (auto-reload enabled)...")
    uvicorn.run("prism.api:app", host=args.host, port=args.port, reload=True, log_level="info")


if __name__ == "__main__":
    main()

