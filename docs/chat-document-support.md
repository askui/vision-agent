# Chat Document Support

## Supporting Files

### Use Cases & Scenarios

#### Sunny Case

1. User inserts file into chat input
2. Upload files through files API --> We back the files ids.
3. We built up files message contents (custom message content blocks)
4. Create message with the custom message content blocks and run it
5. Inside the Runner we remap the files content blocks to other content blocks supported by Anthropic Claude Sonnet (main model we are using)

How do we do the mapping in 5.?
- We do lazy/cached mapping
    - If we have not yet extracted the contents of the file, we extract them.
    - We save them together with the file or the message (as metadata)

Limitations:
- Only supported textual content (even if documents include images)

#### Other Cases

- User uploads and removes file again --> Delete the file from the files API

### Iteration 0

- Just support sunny case --> ignore deletions.
- No lazy/cached mapping --> but run extraction on every single run
- No support of PDFs but only markitdown supported stuff that does not need model

Hub:
1. Add create files API to hub API client
2. Call it to upload file when someone adds file to chat input
3. Make chat input support files we support
4. Construct files message content blocks
5. Loading overview for showing it in chat
6. Loading file when click on overview


AskUI Vision Agent - Chat API:
1. Support files message content blocks
2. Implement the mapping by using the `MessageTranslator`

