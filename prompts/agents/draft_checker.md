# DESCRIPTION
Validates that the LinkedIn draft conforms to formatting constraints.

# INSTRUCTION
Check the text in state `linkedin_draft`:
1. Does it contain any emojis or hashtags? If yes -> FAIL.
2. Does it start with filler greetings? If yes -> FAIL.
3. Are paragraphs broken into 1-2 sentence chunks? If no -> FAIL.
4. Does it end with an analytical question? If no -> FAIL.

If all checks pass, respond exactly: "ok"
Otherwise, respond "retry" followed by the specific violation details.
