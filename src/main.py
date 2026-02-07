import asyncio
import sys
from cli import AnimeDL


def main():
    try:
        app = AnimeDL()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
