# Layout Guide for StocksTUI Application

This document provides a comprehensive guide to layout techniques in the StocksTUI application, which is built using the Textual framework for terminal user interfaces. It covers CSS properties, layout techniques, common pitfalls, and practical examples based on our experience with the application.

## Table of Contents

1. [Textual Layout Fundamentals](#textual-layout-fundamentals)
2. [CSS Properties in Textual](#css-properties-in-textual)
3. [Layout Techniques](#layout-techniques)
4. [Vertical Alignment Strategies](#vertical-alignment-strategies)
5. [Spacing and Margins](#spacing-and-margins)
6. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)

## Textual Layout Fundamentals

The Textual framework uses a combination of Python code and CSS-like styling to create terminal user interfaces. Understanding these fundamentals is crucial for effective layout:

### Container Types

- **Vertical**: Arranges children vertically (top to bottom)
- **Horizontal**: Arranges children horizontally (left to right)
- **Container**: Generic container that can be styled with CSS

Example from `portfolio_view.py`:
```python
# Portfolio selector and management buttons
with Horizontal(id="portfolio-header", classes="portfolio-header"):
    yield Label("Portfolio:", id="portfolio-label", classes="portfolio-label")
    yield Select([], id="portfolio-select")
    yield Button("New", id="new-portfolio")
    yield Button("Edit", id="edit-portfolio")
    yield Button("Delete", id="delete-portfolio", variant="error")
```

### Layout Properties

- **layout**: Defines how children are arranged (`vertical`, `horizontal`)
- **height**: Controls the height of an element (`auto`, `1fr`, or specific units)
- **width**: Controls the width of an element (`auto`, `1fr`, or specific units)

Example from `main.css`:
```css
#app-body {
  layout: vertical;
  height: 1fr; /* Takes up all available vertical space */
}
```

## CSS Properties in Textual

Textual uses a CSS-like syntax for styling, but with some important differences from web CSS:

### Key Properties

- **margin/padding**: Uses integer values (no decimals or units)
- **align**: Controls alignment of content within a container
- **content-align**: Controls alignment of text within an element
- **dock**: Pins an element to a specific edge of its container

### Value Types

- **Integer values**: Used for margins, padding, heights (e.g., `margin-top: 1`)
- **Fractional values**: Used for flexible sizing (e.g., `width: 1fr`)
- **Tuples for alignment**: Used as pairs for horizontal/vertical alignment (e.g., `align: ("left", "middle")`)

### Important Note

Textual CSS does not support floating-point values for properties like margin and padding. Always use integer values:

```css
/* CORRECT */
.portfolio-label {
  margin-top: 1;
}

/* INCORRECT - will cause errors */
.portfolio-label {
  margin-top: 0.5;
}
```

## Layout Techniques

### Flexible Layouts

Use `1fr` (fraction) to create flexible layouts that adapt to available space:

```css
#portfolio-selector {
  width: 1fr; /* Takes up all available width */
  margin-right: 1;
}
```

### Fixed vs. Auto Sizing

- **Fixed sizing**: Specify exact dimensions (e.g., `height: 3`)
- **Auto sizing**: Let content determine size (e.g., `height: auto`)
- **Fractional sizing**: Take up available space (e.g., `height: 1fr`)

Example:
```css
.portfolio-header {
  height: 3; /* Fixed height for the header */
}

.portfolio-controls {
  height: auto; /* Let the height adjust to content */
}

#output-container {
  height: 1fr; /* Takes up all available vertical space */
}
```

### Nesting Containers

Nest containers to create complex layouts:

```python
# Main container
with Vertical(id="portfolio-container"):
    # Header section
    with Horizontal(id="portfolio-header"):
        # Header content
    
    # Content section
    with Vertical(id="portfolio-content"):
        # Content elements
```

## Vertical Alignment Strategies

Achieving proper vertical alignment is often challenging. Here are effective strategies:

### 1. Using `align` Property

For container elements, use the `align` property with tuples:

```python
portfolio_header.styles.align = ("left", "middle")
```

### 2. Using `content-align` Property

For text elements like labels, use the `content-align` property:

```python
portfolio_label.styles.content_align = ("center", "middle")
```

### 3. Using Margins for Fine-tuning

When alignment properties aren't enough, use margins to adjust position:

```python
portfolio_label.styles.margin_top = 1
```

## Spacing and Margins

### Positive vs. Negative Margins

- **Positive margins**: Create space between elements
- **Negative margins**: Reduce space or create overlaps

Example:
```css
/* Add separation between header and content */
#portfolio-content {
  margin-top: 1;
}

/* Reduce space between content and buttons */
#stock-buttons {
  margin-top: -1;
}
```

### Controlling Whitespace

Use a combination of margins, padding, and heights to control whitespace:

```css
.portfolio-controls {
  height: auto;
  layout: horizontal;
  align: left middle;
  padding: 0 1; /* Horizontal padding only */
}
```

## Common Pitfalls and Solutions

### Pitfall 1: Floating-point Values

**Problem**: Using floating-point values for margins or padding causes errors.

**Solution**: Always use integer values.

```python
# INCORRECT
portfolio_label.styles.margin_top = 0.5  # Will cause ValueError

# CORRECT
portfolio_label.styles.margin_top = 1
```

### Pitfall 2: Incorrect Tuple Format

**Problem**: Using strings instead of tuples for alignment properties.

**Solution**: Use proper tuple format.

```python
# INCORRECT
portfolio_label.styles.content_align = "center middle"  # Will cause ValueError

# CORRECT
portfolio_label.styles.content_align = ("center", "middle")
```

### Pitfall 3: Missing IDs for Element Selection

**Problem**: Unable to select elements for styling in code.

**Solution**: Always add IDs to elements you need to manipulate.

```python
# GOOD PRACTICE
with Vertical(id="portfolio-content", classes="portfolio-content"):
    # Now can be selected with self.query_one("#portfolio-content")
```

### Pitfall 4: Inconsistent Styling Between CSS and Python

**Problem**: Styles applied in Python code don't match CSS.

**Solution**: Keep styles consistent or prioritize one approach.

```python
# In Python code
portfolio_content.styles.margin_top = 1

# In CSS - should match Python code
#portfolio-content {
  margin-top: 1;
}
```

## Code Examples

### Example 1: Vertically Centering a Label Next to a Control

```python
# In portfolio_view.py
with Horizontal(id="portfolio-header", classes="portfolio-header"):
    yield Label("Portfolio:", id="portfolio-label", classes="portfolio-label")
    yield Select([], id="portfolio-select")

def on_mount(self) -> None:
    # Vertically center the portfolio label
    portfolio_label = self.query_one("#portfolio-label")
    portfolio_label.styles.margin_top = 1
    
    # Ensure the header has proper vertical alignment
    portfolio_header = self.query_one("#portfolio-header")
    portfolio_header.styles.align = ("left", "middle")
```

```css
/* In main.css */
.portfolio-label {
  margin-top: 1;
}

.portfolio-header {
  align-vertical: middle;
}
```

### Example 2: Creating Separation Between Elements

```python
# In portfolio_view.py
def on_mount(self) -> None:
    # Add separation between header and content
    portfolio_content = self.query_one("#portfolio-content")
    portfolio_content.styles.margin_top = 1
```

```css
/* In main.css */
#portfolio-content {
  margin-top: 1;
}
```

### Example 3: Reducing Spacing for Compact Layout

```python
# In portfolio_view.py
def on_mount(self) -> None:
    # Reduce space between content and buttons
    stock_buttons = self.query_one("#stock-buttons")
    stock_buttons.styles.margin_top = -1
```

```css
/* In main.css */
#stock-buttons {
  margin-top: -1;
}
```

## Best Practices

1. **Use IDs and Classes Consistently**
   - Use IDs for unique elements (`id="portfolio-header"`)
   - Use classes for styling groups of elements (`classes="portfolio-label"`)

2. **Apply Base Styles in CSS**
   - Keep common styles in CSS for maintainability
   - Use Python for dynamic or conditional styling

3. **Use Semantic Container Structure**
   - Organize elements in logical containers
   - Use appropriate container types (Vertical/Horizontal)

4. **Document Layout Decisions**
   - Add comments explaining complex layout choices
   - Use consistent naming conventions

5. **Test on Different Terminal Sizes**
   - Ensure layouts work on various terminal dimensions
   - Use fractional sizing (`1fr`) for adaptable layouts

6. **Prefer Declarative Layout in Python**
   - Define structure clearly in the `compose()` method
   - Use `on_mount()` for fine-tuning styles

7. **Handle Errors Gracefully**
   - Use try/except blocks when applying styles
   - Check for element existence before styling

```python
try:
    portfolio_label = self.query_one("#portfolio-label")
    portfolio_label.styles.margin_top = 1
except NoMatches:
    # Handle case where element doesn't exist
    pass
```

By following these guidelines and techniques, you can create well-structured, visually appealing terminal user interfaces in the StocksTUI application using the Textual framework.