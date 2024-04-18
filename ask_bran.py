import argparse

from app.bran import Bran


def ask_multiline(help_text: str = "") -> str:
    print(help_text)
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break
    return '\n'.join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", help="Default language", default="English")
    parser.add_argument("--prompt", help="What to ask Bran for", required=False)
    args = parser.parse_args()

    prompt = args.prompt if args.prompt else ask_multiline("Please finish your input with an empty line.\n"
                                                           "What do you want to ask Bran for?")

    bran = Bran(language=args.lang)
    bran.execute(objective=prompt)
