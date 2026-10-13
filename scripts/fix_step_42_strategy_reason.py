from pathlib import Path

path = Path(r"C:\Projects\sunwise-koyash\backend\app\algorithms\replacement_strategy.py")
text = path.read_text(encoding="utf-8")

if '"strategy_reason"' not in text:
    old = '                "replacement_reason": REASON_LABELS.get(reason, REASON_LABELS["other"]),'
    new = '''                "replacement_reason": REASON_LABELS.get(reason, REASON_LABELS["other"]),
                "strategy_reason": REASON_LABELS.get(reason, REASON_LABELS["other"]),'''
    if old not in text:
        raise RuntimeError("Could not find replacement_reason insertion point")
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("Step 4.2 fixed: strategy_reason added to replacement candidates.")