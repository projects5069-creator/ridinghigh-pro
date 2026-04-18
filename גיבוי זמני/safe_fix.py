
import sys

DASH = '/Users/adilevy/RidingHighPro/dashboard.py'
FUNC = '/Users/adilevy/RidingHighPro/_st_func.py'

lines = open(DASH, encoding='utf-8', errors='replace').readlines()
func  = open(FUNC, encoding='utf-8').read()

TARGET_EMOJI = '\U0001f3af'  # 🎯

new = []
func_inserted = False

for i, l in enumerate(lines):
    n = i + 1

    # Insert function before def main()
    if not func_inserted and l.rstrip() == 'def main():':
        new.append(func + '\n\n')
        func_inserted = True
        print(f'[OK] func inserted before line {n}')

    # Fix nav list line 2497
    if n == 2497:
        l = '        ["\U0001f4ca Live Tracker", "\U0001f4bc Portfolio Tracker", "\U0001f3af Portfolio Score Tracker", "\U0001f4c5 Daily Summary", "\U0001f4e6 Timeline Archive", "\U0001f52c Post Analysis"]\n'
        print('[OK] nav fixed')

    # Fix elif line 2513  
    if n == 2513:
        l = '    elif page == "\U0001f3af Portfolio Score Tracker":\n'
        print('[OK] elif fixed')

    new.append(l)

if not func_inserted:
    print('[ERR] def main() not found!')
    sys.exit(1)

open(DASH, 'w', encoding='utf-8').writelines(new)
print('[OK] Done')
