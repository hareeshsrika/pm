from .config import get_settings
from .openrouter import ask_openrouter


def main() -> None:
    settings = get_settings()
    answer = ask_openrouter(
        "What is 2 + 2? Reply with only the number 4.",
        settings.openrouter_api_key,
    )
    print(answer)


if __name__ == "__main__":
    main()
