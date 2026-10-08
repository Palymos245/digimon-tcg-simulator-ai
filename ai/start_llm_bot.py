from decouple import config

from LLMBeelzemonBot import LLMBeelzemonBot


def main() -> None:
    bot = LLMBeelzemonBot(config("BOT_USERNAME"))
    login_response = bot.login()
    print(login_response)
    if not login_response:
        print("Login failed, registering the bot")
        register_response = bot.register()
        if not register_response:
            raise SystemExit(1)
        login_response = bot.login()
        if not login_response:
            raise RuntimeError("Login failed after registration!")

    if not bot.set_avatar(config("BOT_AVATAR")):
        raise SystemExit(1)

    imported_decks = bot.list_imported_decks()
    if not imported_decks:
        raise SystemExit(1)
    imported_decks = imported_decks.json()

    if not bot.import_deck(imported_decks):
        raise SystemExit(1)
    if not bot.set_active_deck():
        raise SystemExit(1)

    bot.join_lobby()


if __name__ == "__main__":
    main()
