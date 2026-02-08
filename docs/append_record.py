import pandas as pd

# ---------- CONFIG ----------
RECORD_PATH = "record.csv"
STANDINGS_PATH = "Fantrax-Standings-Fantrax Breakaway Super League.csv"
MAX_GW = 25
OUTPUT_PATH = "record_appended_up_to_gw25.csv"
# ----------------------------

GW_DATES = {
    1:  ("Fri Aug 15, 2025", "Thu Aug 21, 2025"),
    2:  ("Fri Aug 22, 2025", "Thu Aug 28, 2025"),
    3:  ("Fri Aug 29, 2025", "Thu Sep 11, 2025"),
    4:  ("Fri Sep 12, 2025", "Thu Sep 18, 2025"),
    5:  ("Fri Sep 19, 2025", "Thu Sep 25, 2025"),
    6:  ("Fri Sep 26, 2025", "Thu Oct 2, 2025"),
    7:  ("Fri Oct 3, 2025",  "Thu Oct 16, 2025"),
    8:  ("Fri Oct 17, 2025", "Thu Oct 23, 2025"),
    9:  ("Fri Oct 24, 2025", "Thu Oct 30, 2025"),
    10: ("Fri Oct 31, 2025", "Thu Nov 6, 2025"),
    11: ("Fri Nov 7, 2025",  "Thu Nov 20, 2025"),
    12: ("Fri Nov 21, 2025","Thu Nov 27, 2025"),
    13: ("Fri Nov 28, 2025","Mon Dec 1, 2025"),
    14: ("Tue Dec 2, 2025", "Thu Dec 4, 2025"),
    15: ("Fri Dec 5, 2025", "Thu Dec 11, 2025"),
    16: ("Fri Dec 12, 2025","Thu Dec 18, 2025"),
    17: ("Fri Dec 19, 2025","Thu Dec 25, 2025"),
    18: ("Fri Dec 26, 2025","Sun Dec 28, 2025"),
    19: ("Mon Dec 29, 2025","Thu Jan 1, 2026"),
    20: ("Fri Jan 2, 2026", "Mon Jan 5, 2026"),
    21: ("Tue Jan 6, 2026", "Thu Jan 15, 2026"),
    22: ("Fri Jan 16, 2026","Thu Jan 22, 2026"),
    23: ("Fri Jan 23, 2026","Thu Jan 29, 2026"),
    24: ("Fri Jan 30, 2026","Thu Feb 5, 2026"),
    25: ("Fri Feb 6, 2026","Mon Feb 9, 2026"),
}

# Load files
record = pd.read_csv(RECORD_PATH)

raw = pd.read_csv(
    STANDINGS_PATH,
    header=None,
    engine="python",
    names=[0, 1, 2, 3],
    on_bad_lines="skip"
)


print("Raw rows loaded:", len(raw))
print(raw[raw[0].astype(str).str.startswith("Gameweek")].head())


parsed_rows = []
i = 0
current_gw = None

# Parse Fantrax stacked format
while i < len(raw):
    cell = raw.iloc[i, 0]

    if isinstance(cell, str) and cell.startswith("Gameweek"):
        current_gw = int(cell.split()[1])
        i += 2  # skip header row ("Away FPts Home FPts")
        continue

    if current_gw is not None and current_gw <= MAX_GW:
        try:
            away = raw.iloc[i, 0]
            away_pts = float(raw.iloc[i, 1])
            home = raw.iloc[i, 2]
            home_pts = float(raw.iloc[i, 3])

            parsed_rows.append({
                "Gameweek": current_gw,
                "Away": away,
                "AwayScore": away_pts,
                "Home": home,
                "HomeScore": home_pts
            })
        except Exception:
            pass

    i += 1

fixtures = pd.DataFrame(parsed_rows)

# Convert to record.csv format (two rows per fixture)
new_rows = []

for _, r in fixtures.iterrows():

    if r.Gameweek not in GW_DATES:
        raise ValueError(f"Missing hard-coded dates for Gameweek {r.Gameweek}")

    start_date, end_date = GW_DATES[r.Gameweek]

    new_rows.append({
        "Gameweek": r.Gameweek,
        "Start_Date": start_date,
        "End_Date": end_date,
        "Team": r.Away,
        "Score": r.AwayScore,
        "Opponent": r.Home,
        "Opp_Score": r.HomeScore
    })

    new_rows.append({
        "Gameweek": r.Gameweek,
        "Start_Date": start_date,
        "End_Date": end_date,
        "Team": r.Home,
        "Score": r.HomeScore,
        "Opponent": r.Away,
        "Opp_Score": r.AwayScore
    })


new_df = pd.DataFrame(new_rows)

# Append + deduplicate (safety first)
combined = pd.concat([record, new_df], ignore_index=True)

combined = combined.drop_duplicates(
    subset=["Gameweek", "Team", "Opponent", "Score", "Opp_Score"],
    keep="first"
)

combined = combined.sort_values(["Gameweek", "Team"]).reset_index(drop=True)

# Save output
combined.to_csv(OUTPUT_PATH, index=False)

print("Done.")
print(f"Final max gameweek: {combined.Gameweek.max()}")
print(f"Total rows: {len(combined)}")
print(f"Output written to: {OUTPUT_PATH}")

