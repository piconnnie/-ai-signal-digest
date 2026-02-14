---
inclusion: always
---
# Core Behavioral Rules

## Planning
•⁠  ⁠Find multiple approaches, ask for confirmation before coding.
•⁠  ⁠Do NOT generate code while planning, only define approach.
•⁠  ⁠Use progress.md checklist to plan, track, and mark complete.
•⁠  ⁠If unsure, perform web search to validate API, command, or approach.

## Coding
•⁠  ⁠Update progress.md before starting (checklist of tasks).
•⁠  ⁠Do NOT change comments unless explicitly asked.
•⁠  ⁠Do NOT generate documentation unless explicitly asked.
•⁠  ⁠Keep summary as bullet points — no fluff.
•⁠  ⁠When fixing bugs, use parallel invocations for multiple independent changes.
•⁠  ⁠When user says "understood", acknowledge and wait — no extra work.

## Debugging
•⁠  ⁠Wait for specific error details before proceeding on "still some error".
•⁠  ⁠Find all occurrences of problematic patterns across codebase, fix all at once.
•⁠  ⁠Check working examples in codebase to find correct API usage patterns.
•⁠  ⁠Verify fixes by searching for the pattern again after changes.

## Principles

### Think Before Coding
•⁠  ⁠State assumptions explicitly. If uncertain, ask.
•⁠  ⁠If multiple interpretations exist, present them — don't pick silently.
•⁠  ⁠If a simpler approach exists, say so. Push back when warranted.

### Simplicity First
•⁠  ⁠Minimum code that solves the problem. Nothing speculative.
•⁠  ⁠No abstractions for single-use code. No unrequested flexibility.
•⁠  ⁠If 200 lines could be 50, rewrite it.

### Surgical Changes
•⁠  ⁠Touch only what you must. Match existing style.
•⁠  ⁠Don't improve adjacent code, comments, or formatting.
•⁠  ⁠Remove only orphans YOUR changes created.

### Goal-Driven Execution
•⁠  ⁠Transform tasks into verifiable goals with success criteria.
•⁠  ⁠For multi-step tasks, state a brief plan with verification checks.

## Tool Preferences
•⁠  ⁠Docker: use ⁠ finch ⁠ instead of ⁠ docker ⁠ locally.
•⁠  ⁠Web server: always use Flask (even for websocket).
•⁠  ⁠Never put large data or multi-line code inline in bash commands — write to a ⁠ .py ⁠ file in ⁠ temp/ ⁠ then run it.

## Hooks
•⁠  ⁠Keep hook prompts focused and single-purpose — no mega-prompts.
•⁠  ⁠For complex multi-phase hooks, use structured steps (STEP 1, STEP 2...) with explicit categories to scan — not vague "review what happened."
•⁠  ⁠Delete and replace bad hooks entirely — don't try to patch bloated ones.
•⁠  ⁠For global file writes (~/.kiro/steering/): write clean file to workspace ⁠ temp/ ⁠, then ⁠ mv temp/file.md ~/.kiro/steering/file.md ⁠. Avoid ⁠ sed -i '' ⁠ for multiline edits — it corrupts lines on macOS.