import asyncio
from cli import AnimeDL


def main():
    app = AnimeDL()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
