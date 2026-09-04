# Contributing to BNGIS 🇮🇳

Thank you for considering contributing to the Bharath Neuro-Governance Intelligence System!

## Ways to help

- 🗂️ **Scheme data** — add more state schemes to `app/data/schemes.json` (with official source links)
- 🗣️ **Language NLP** — extend lexicons in `app/engines/voice.py` (more Indian languages welcome!)
- 🗺️ **Resource data** — add facilities for your district in `app/engines/resources.py`
- 🎨 **UI/UX** — the frontend is dependency-free vanilla JS/CSS; improvements welcome
- 🧪 **Tests** — more test cases in `tests/` (pytest)
- 📚 **Docs** — fix typos, translate documentation

## Development setup

```bash
git clone https://github.com/joyboyzz/BNGIS-AI-Governance.git
cd BNGIS-AI-Governance
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v                      # run the test suite
python3 -m uvicorn app.main:app --reload --port 8000
```

## Ground rules

1. Run `pytest tests/` before committing — all 25+ tests must pass.
2. Keep the **zero-dependency** philosophy for the core engines (pure Python + stdlib).
3. No paid APIs. No PII in demo data. Keep everything deterministic (seeded random).
4. Small, focused pull requests with clear descriptions.

## Commit style

Emoji-prefixed conventional commits, e.g.:

```
✨ add epidemic scenario comparison chart
🐛 fix SEIR population conservation
📖 update README demo flow
```
