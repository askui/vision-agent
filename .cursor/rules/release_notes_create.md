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

2. Create a list of all changes that follows the schema defined in @.cursor/rules/release_notes_schema.json

DO NOT EXAMINE COMMITS

instead

```bash
git diff --name-status $LAST_TAG..HEAD
```

Go over all files from top to bottom in the diff.

- if the file still was not deleted or only moved, extract and analyze the diff using `git diff $LAST_TAG..HEAD <path_to_file>`
- update the list of changes by proposing a patch using JSON Patch operations following RFC 6902, e.g.,
  ```json
  [
    {
      "op": "add",
      "path": "/changes/-",
      "value": {
        "type": "feat",
        "module": "askui",
        "summary": "add new agent WebVisionAgent",
        "content": [
          "interact with web pages using [playwright](https://playwright.dev/)"
        ],
        "breaking": false
      }
    },
    {
      "op": "addd",
      "path": "/changes/-",
      "value": {
        "type": "fix",
        "module": "askui.models.askui",
        "summary": "load AskUiInferenceApiSettings from environment",
        "content": [
          "switch env variable prefix from `ASKUI_` to `ASKUI__`",
          "set `AskUiInferenceApiSettings` using env variables `ASKUI__MESSAGES__MODEL`, `ASKUI__MESSAGES__BETAS` etc. (exploded settings) instead of only being able to set them using, e.g., `ASKUI__MESSAGES` (as json string)",
          "keep env variables mostly used working (validation alias): `ASKUI_TOKEN`, `ASKUI_WORKSPACE_ID`, `ASKUI_INFERENCE_ENDPOINT`"
        ],
        "breaking": true
      }
    }
  ]
  ```

GENERATE A PATCH BEFORE MOVING FROM ONE FILE TO THE NEXT FILE
