from datetime import timedelta
from pathlib import Path

def parse_hhmm(s):
	parts = s.strip().split(":")
	if len(parts) != 2:
		raise ValueError("Please enter time as HH:MM")
	h, m = int(parts[0]), int(parts[1])
	return h * 60 + m

length_str = input("Enter total length (HH:MM): ").strip()
total_minutes = parse_hhmm(length_str)
total_seconds = total_minutes * 60

filename = input("Enter output filename (e.g. timestamps.tsv): ").strip()
out_path = Path(__file__).parent / "Data" / filename
out_path.parent.mkdir(exist_ok=True)

with open(out_path, "w", encoding="utf-8", newline="") as f:
	f.write("timestamp\n")
	for sec in range(0, total_seconds + 1, 5):
		t = str(timedelta(seconds=sec)).rjust(8, "0")
		f.write(f"{t}\n")

print(f"Written to: {out_path}")
