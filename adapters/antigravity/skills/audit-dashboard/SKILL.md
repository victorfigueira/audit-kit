---
name: audit-dashboard
description: >-
  Generate and open the interactive standalone HTML/CSS/JS dashboard for audit-kit findings and snapshots.
---

# Interactive Audit Dashboard

Generate and surface the standalone, zero-dependency HTML dashboard from audit-kit.

## Procedure
1. Run the dashboard generator script:
   ```bash
   python3 audit-kit/tools/generate_dashboard.py
   ```
2. Confirm that `audit/dashboard.html` was generated.
3. Inform the user of the path and provide a clickable file link to `audit/dashboard.html` (`file://...`) which can be opened directly in any web browser.
