import re

path = '/Users/adilevy/RidingHighPro/dashboard.py'
lines = open(path).readlines()

# Remove bad lines injected by sed (lines starting with single space + score_tracker or elif or else)
clean = []
for line in lines:
    stripped = line.rstrip()
    # Skip bad injected lines (start with single space only)
    if (stripped.startswith(' score_tracker_page') or
        stripped == ' elif page == "\u1f77\u1f6f Score Tracker":' or
        stripped.startswith(' elif page ==') or
        stripped.startswith(' else:')):
        print(f'REMOVED: {stripped[:30]}...')
        continue
    clean.append(line)

open(path, 'w').writelines(clean)
print(f'Done! {len(lines)-len(clean)} lines removed')
