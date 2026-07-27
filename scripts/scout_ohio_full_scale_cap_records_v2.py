"""Narrow selector fix for the one-off Ohio cap-record scout."""
from __future__ import annotations

import scout_ohio_full_scale_cap_records as scout


def locate_full_text_input(page):
    field = page.locator("#ctl00_search_txtFullText")
    if field.count() != 1:
        raise RuntimeError(
            f"Expected one Ohio full-text field, found {field.count()}"
        )
    return field


scout.locate_full_text_input = locate_full_text_input

if __name__ == "__main__":
    raise SystemExit(scout.main())
