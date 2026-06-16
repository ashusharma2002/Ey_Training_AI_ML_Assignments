Cleanup performed on branch `root`

- Date: 2026-06-16
- Actions taken:
  - Removed Groq and LangSmith secrets from Git history using `git-filter-repo`.
  - Rewrote history and force-pushed cleaned `root` branch to `origin`.
  - Replaced embedded tokens in notebooks with environment-variable placeholders.
  - Added common large-file patterns to `.gitignore`.
- Recommended next steps:
  1. Rotate the exposed Groq and LangSmith tokens immediately.
  2. Inform collaborators to re-clone the repository (history was rewritten).
  3. Delete any local backups that may contain the old secrets.

If you want, I can also create a PR with these changes or push any further cleanup commits.
