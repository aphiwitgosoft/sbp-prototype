import re
import json

with open('/Users/bank_mac/gosoft/java/SBP/sbp-prototype/plan-api.html', 'r', encoding='utf-8') as f:
    content = f.read()

# I will do a regex replacement or text replacement for a few key endpoints to add `sql` and `flowchart`.
# Actually, I can use a simpler approach. Just replace the whole script block or inject code in `plan-api.html`
