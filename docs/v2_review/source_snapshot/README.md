# Oblivion v2 source snapshot

This directory contains the release-critical v2 translation artifacts recovered from the original Steam Deck worktree.

Tracked here because `v2_work/` is intentionally ignored as a large local workspace.

## Source of truth

- `V2_SOL_FINAL_OVERRIDE.csv`: 9,049 GPT-5.6 Sol-reviewed v2 overrides (MASTER 8,553 + BOOK 496).
- `GMST_REUSE_V1_926.csv`: retained menu GMST source used by the v2 pipeline.
- `BOOK_FINAL_REVIEWED.csv` / `BOOK_FINAL_TRANSLATIONS.json`: final reviewed BOOK data.
- Coverage and export reports record the completed v2 state.

The full local workspace also contains generated Gemini batches, intermediate review ledgers, Japanese references, test builds, logs, and API credentials. Those are not release inputs and are deliberately not committed here.

## Rule for future releases

Any file required to reproduce a public release must live in a tracked repository path or be generated deterministically from tracked inputs. A release builder must not depend on ignored `v2_work/` files or private API-key files.
