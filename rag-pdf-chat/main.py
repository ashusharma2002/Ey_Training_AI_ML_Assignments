"""
main.py
CLI entry point. Run this to build the index once, then chat in a loop.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from pipeline import build_index, get_answer


def main():
    print("=" * 50)
    print("RAG PDF Chat — CLI")
    print("=" * 50)

    choice = input("Build/rebuild the index from data/pdfs? (y/n): ").strip().lower()
    if choice == "y":
        build_index()

    print("\nType your questions below. Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not question:
            continue

        answer, sources = get_answer(question)
        print(f"\nAssistant: {answer}\n")
        if sources:
            print("Sources:")
            for s in sources:
                print(" -", s)
        print()


if __name__ == "__main__":
    main()
