# Portfolio View Scrolling Fix

## Date: 2025-07-13

## Issue Description

In the StocksTUI application, users have reported that when adding a large number of stocks to a portfolio, they are unable to see all the stocks even when attempting to scroll. This indicates a UI limitation in the portfolio view that prevents proper scrolling behavior.

## Root Cause Analysis

After investigating the code, I've identified the root cause of this issue:

1. In `portfolio_view.py`, the portfolio data is displayed in a `DataTable` within a `Vertical` container with ID `portfolio-content`.

2. In the CSS file (`main.css`), there are styling issues:
   - `#portfolio-table` has `height: auto`, which means it will expand to fit its content without enabling scrolling.
   - `#portfolio-content` doesn't have any overflow or scrolling properties defined.
   - There is a `#portfolio-container` selector with proper scrolling properties (`overflow: auto`), but this ID isn't used in the `PortfolioView` class.

This mismatch explains why users can't see all stocks even when scrolling - the container that holds the table doesn't have scrolling enabled, and the table itself is set to expand indefinitely rather than scroll.

## Proposed Solution

There are two possible approaches to fix this issue:

### Option 1: CSS Modification (Recommended)

Modify `main.css` to add overflow and scrolling properties to the `#portfolio-content` container:

```css
#portfolio-content {
  margin-top: 1;
  height: 1fr;
  overflow: auto;
  scrollbar-color: $panel;
  scrollbar-color-hover: $accent;
}
```

This change will allow the portfolio content container to scroll when it contains more stocks than can fit in the visible area.

### Option 2: Python Code Modification

Alternatively, modify `portfolio_view.py` to add the ID `portfolio-container` to the main `PortfolioView` class:

```python
class PortfolioView(Vertical):
    """A view for displaying and managing portfolios of stocks."""
    
    def __init__(self):
        super().__init__(id="portfolio-container")
```

This would leverage the existing CSS rule for `#portfolio-container` which already has the necessary overflow and scrolling properties.

## Implementation Recommendation

Option 1 (CSS modification) is recommended as it's less intrusive and doesn't require changing the Python code structure. This approach maintains the existing container hierarchy while adding the necessary scrolling behavior to the content container.

## Implementation Status

The recommended CSS modification (Option 1) has been implemented in `stockstui/main.css`.

**Verification:** The fix has been tested by adding a large number of stocks to a portfolio, and all stocks are now visible and the table is scrollable. The issue is resolved.

## Additional Improvements

After implementing the initial fix, we noticed that there was still unused vertical space at the bottom of the Portfolio tab. To better utilize this space and make the stock list area larger, we made the following additional improvement:

```css
#portfolio-content {
  margin-top: 1;
  height: 1fr;
  min-height: 30; /* Add minimum height to ensure the content area is larger */
  overflow: auto;
  scrollbar-color: $panel;
  scrollbar-color-hover: $accent;
}
```

By adding a `min-height: 30;` property, we ensure that the portfolio content container takes up more vertical space, making better use of the available screen real estate and allowing users to see more stocks at once without scrolling.