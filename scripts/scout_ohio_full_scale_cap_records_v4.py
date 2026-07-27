"""One-line Playwright compatibility fix for the restricted Ohio inventory."""
from __future__ import annotations

import scout_ohio_full_scale_cap_records_v3 as scout


def set_page_size_600(page) -> None:
    selector = page.locator(scout.PAGE_SIZE)
    if selector.count() != 1:
        return
    current = selector.input_value()
    if current == "600":
        return
    before = page.locator(scout.RESULT_LINK).count()
    selector.select_option("600")
    page.wait_for_timeout(3500)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_function(
        """({selector, before}) => {
          const sel = document.querySelector(selector);
          const count = document.querySelectorAll("a[onclick*='ViewDocument.aspx?docid=']").length;
          return !sel || sel.value === '600' || count !== before;
        }""",
        arg={"selector": scout.PAGE_SIZE, "before": before},
        timeout=60000,
    )
    page.wait_for_timeout(1500)


scout.set_page_size_600 = set_page_size_600

if __name__ == "__main__":
    raise SystemExit(scout.main())
