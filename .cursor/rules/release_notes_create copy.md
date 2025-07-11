---
description: Create release notes for a new Github release
globs:
alwaysApply: false
---

Please follow the steps below in the order they are listed to create release notes for a new Github release.

1. Retrieve the last release tag (e.g. `v1.0.0`)
  ```bash
  git tag --sort=-version:refname | head -1
  ```

2. Diff changes since last release (DO NOT EXAMINE COMMITS)
  ```bash
  # Show full diff since last release
  git diff --name-status $LAST_TAG..HEAD
  ```

3. Create a list of all changes since the last release by going through all the files from top to bottom in the diff done in previous step one by one
  - If the file exists, examine all the changes of the file by going through the file diff `git diff $LAST_TAG..HEAD <path_to_file>` and go through the changes one by one
  - For each change, decide wether it is already included in the list of changes and depending on that
    either add it to the list or update the list item
  - Output the patch of the updated list of changes after each processed change, e.g.,
    ```markdown
    Processing <path_to_file>

    Still exists

    Run `git diff $LAST_TAG..HEAD <path_to_file>` to see the changes

    Patch of updated list of changes:
    - <list of changes>

    Processing <path_to_file>

    Still exists

    Run `git diff $LAST_TAG..HEAD <path_to_file>` to see the changes

    Patch of updated list of changes:
    - <list of changes>

    etc.
    ```
  - Each list item should have the following format:
    ```markdown
    - <type_of_change: feat, fix, refactor, docs, chore, perf, test, build, ci, other>(<module of if outside `src`, the path or omit>)<"!" if breaking change>: <summary of description in imperative mood>

      <long form description of the change + update instructions if breaking change>
    ```
  - A breaking change is a change that changes the API, the configuration (e.g., the env variables) that the consumer of the library interacts with in way that may break the existing code or changes the behavior that may lead to unexpected results
  - Code references should be in formated as code using backticks, e.g., `code`, or code blocks
  - Example:
    ```markdown
    - feat(askui): add new agent `WebVisionAgent`

      - interact with web pages using [playwright](https://playwright.dev/)

    - fix(askui.models.askui)!: load `AskUiInferenceApiSettings` from environment

      - switch env variable prefix from `ASKUI_` to `ASKUI__`
      - set `AskUiInferenceApiSettings` using env variables `ASKUI__MESSAGES__MODEL`, `ASKUI__MESSAGES__BETAS` etc. (exploded settings)
        instead of only being able to set them using, e.g., `ASKUI__MESSAGES` (as json string)
      - keep env variables mostly used working (validation alias): `ASKUI_TOKEN`, `ASKUI_WORKSPACE_ID`, `ASKUI_INFERENCE_ENDPOINT`
    ```

  (DO NOT EXAMINE COMMITS)

4. Define new release version (`$NEW_VERSION`) based on Semver 2 (for major versions < 1, increase minor version by 1 if there is a breaking changes, increase patch version otherwise by 1), e.g., `0.1.0`



Create release notes for a Python library given a diff of changes since the last release and the commit log since the last release.

It should follow the following format and encompass all changes from the diff:
```markdown
### 🚀 New Features
- [List new features if any]

### 🐞 Bug Fixes
- [List bug fixes if any]

### 🔧 Improvements
- [List improvements if any]

### 🚨 Breaking Changes
- [List all breaking changes + upgrade instructions if any]

### 📜 Documentation
- [List documentation updates if any]

### 🔄 Dependencies
- [List dependency updates if any]

### 🧪 Experimental
- [List experimental features if any]
```

Format code as code using backticks and codeblocks.

For links to files use `[link](url)` with `https://github.com/askui/vision-agent/tree/v0.9.0/<path_to_file>` as base url.








