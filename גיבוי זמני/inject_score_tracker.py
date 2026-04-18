import re

path = '/Users/adilevy/RidingHighPro/dashboard.py'

content = open(path).read()

# 1. Add to navigation list
old_nav = '"\ud83d\udd2c Post Analysis"]'
new_nav = '"\ud83d\udd2c Post Analysis", "\ud83c\udf2f Score Tracker"]'
if old_nav in content:
    content = content.replace(old_nav, new_nav, 1)
    print("\u2705 Navigation updated")
else:
    print("\u274c Navigation not found!")

# 2. Add elif block before the final else:
# The main() ends with:
#     else:
#         post_analysis_page()
old_else = '    else:\n        post_analysis_page()'
new_else = '    elif page == "\ud83c\udf2f Score Tracker":\n        score_tracker_page()\n    else:\n        post_analysis_page()'
if old_else in content:
    content = content.replace(old_else, new_else, 1)
    print("\u2705 elif block added")
else:
    print("\u274c else block not found!")

open(path, 'w').write(content)
print("\u2705 Done")
