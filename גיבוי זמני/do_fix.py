import re

DASH = '/Users/adilevy/RidingHighPro/dashboard.py'
FUNC = '/Users/adilevy/RidingHighPro/_st_func.py'

lines = open(DASH, encoding='utf-8', errors='replace').readlines()
func = open(FUNC, encoding='utf-8').read()

EMOJI_TARGET = '\U0001f3af'

new = []
inserted_func = False

for i,l in enumerate(lines):
    n = i + 1

    # Insert function just before def main()
    if not inserted_func and l.rstrip() == 'def main():':
        new.append(func + '\n\n')
        inserted_func = True
        print(f'\u2705 function inserted before line {n}')

    # Fix broken emoji in nav list
    if '\u03af\u1f6f Portfolio Score Tracker' in l:
        l = l.replace('\u03af\u1f6f Portfolio Score Tracker', EMOJI_TARGET + ' Portfolio Score Tracker')
        print(f'\u2705 emoji fixed line {n}')

    new.append(l)

open(DASH, 'w', encoding='utf-8').writelines(new)
print('\u2705 Done')
