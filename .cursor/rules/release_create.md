---
description: Create new Github release
globs:
alwaysApply: false
---

Steps:

- Update version in @src/askui/__init__.py
  ```bash
  # Update version in __init__.py
  sed -i '' "s/__version__ = \"[^\"]*\"/__version__ = \"$NEW_VERSION\"/" src/askui/__init__.py
  ```

- Create commit with message "chore: bump version to <version>" and push to `main` branch
  ```bash
  git add src/askui/__init__.py
  git commit -m "chore: bump version to $NEW_VERSION"
  git push origin main
  ```

- Create a new Github release with the new version and the release notes and save it as draft (DO NOT PUBLISH)
  ```bash
  # Create tag
  git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
  git push origin "v$NEW_VERSION"

  # Create draft release (requires GitHub CLI)
  gh release create "v$NEW_VERSION" --draft --latest --title "v$NEW_VERSION" --notes-file RELEASE_NOTES.md
  ```
