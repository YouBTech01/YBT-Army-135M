# Contributing to YBT Army

Thanks for wanting to help! Anyone can contribute to this repository, from a typo fix to a new feature. You do not need permission first. Just fork the repo and open a pull request.

## Ways to help

- **Test the model** and report wrong, strange or unsafe answers (use the *Bug report* issue form).
- **Improve the UI**: mobile layout, accessibility, animations, new features.
- **Hindi and Hinglish**: better prompts, examples and test questions.
- **Evaluation**: a bigger and fairer test set than our small 20-question check.
- **Training ideas**: datasets, fine-tuning recipes and a larger model with more parameters. Open a Discussion first so we can plan it together.
- **Docs**: clearer setup steps, translations, screenshots.

## Quick workflow

1. Fork this repository and clone your fork.
2. Create a branch: `git checkout -b my-change`.
3. Set up and run the app:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # macOS / Linux: source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run ybt_app.py
   ```
   The model weights use Git LFS, so run `git lfs install` before cloning.
4. Make your change and try it in the browser on desktop and phone width.
5. Commit with a short, clear message and open a pull request. Explain what changed and why.

## Guidelines

- Keep pull requests small and focused. One idea per PR is easiest to review.
- Match the style of the surrounding code.
- Do not commit model weights, chat history (`chats/`), tokens or any private data.
- Changes to the model weights or the system prompt need a Discussion first.
- Be kind. Assume good intent and keep feedback about the work, not the person.

## Licence

By contributing you agree that your contribution is released under the project's [MIT licence](LICENSE).

Questions or ideas? Open an issue or start a Discussion.
