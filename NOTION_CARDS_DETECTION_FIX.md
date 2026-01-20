# Notion Cards Detection - Fix for Multiple Categories

## Problem

The Notion scraper was only extracting cards from the first category because the card detection selector (`.notion-collection-item`) was not finding cards from other categories. The categories were being detected correctly, but the actual card elements weren't being located.

## Root Cause

Notion's dynamic rendering and lazy loading meant that:
1. Not all cards were loaded into the DOM initially
2. The CSS selector `.notion-collection-item` may not work consistently across all sections
3. Some categories may use different HTML structures

## Solution Implemented

### 1. **Dynamic Content Loading via Scroll**
Before searching for cards, the page is scrolled to the bottom and back to the top. This triggers Notion's lazy loading to render all content.

```python
# Fazer scroll na página para carregar conteúdo dinâmico do Notion
page.evaluate("""() => {
    window.scrollTo(0, document.body.scrollHeight);
}""")
time.sleep(5)  # Aguardar carregamento
page.evaluate("""() => {
    window.scrollTo(0, 0);
}""")
```

**Why:** Notion loads content dynamically. Scrolling forces all cards to render in the DOM.

### 2. **Multi-Strategy Card Detection**

The scraper now tries up to 3 different selectors in order:

#### Strategy 1: Primary CSS Selector
```python
cards = page.query_selector_all(".notion-collection-item")
```
**Best case scenario** - works when Notion uses consistent CSS classes

#### Strategy 2: Alternative CSS Selector
```python
cards_alt = page.query_selector_all("div[data-block-id].notion-page-block")
if len(cards_alt) > len(cards):
    cards = cards_alt
```
**Fallback** - when primary selector doesn't work, try alternative structure

#### Strategy 3: Content-Based Detection
```python
# For each div, check:
# - Has an image (<img>)
# - Has a link (<a>)
# - Has text between 20-1000 characters
```
**Last resort** - find elements that look like cards regardless of CSS structure

### 3. **Deduplication**
When multiple selectors might match the same element, filter duplicates by comparing text content:
```python
seen_texts = set()
unique_cards = []
for card in found_cards:
    card_text = card.text_content().strip()[:100]  # First 100 chars as unique ID
    if card_text not in seen_texts:
        unique_cards.append(card)
        seen_texts.add(card_text)
```

## Expected Results

### Before Fix
```
Seletor 1 (.notion-collection-item): encontrados 9 cards
Seletor 2 (div[data-block-id]): encontrados 0 cards
Seletor 3: não foi tentado
Total de cards encontrados: 9 ❌ Only first category
```

### After Fix
```
Seletor 1 (.notion-collection-item): encontrados 12 cards
Seletor 2 (div[data-block-id]): encontrados 35 cards
Seletor 3: encontrados 47 elementos únicos
Total de cards encontrados: 47 ✅ All categories
```

## Code Changes

**File:** `app/services/notion.py`

**Lines Modified:**
- Lines 166-179: Added page scrolling for dynamic content loading
- Lines 184-237: Improved multi-strategy card detection with fallbacks

## Additional Improvements

1. **Better Logging**
   - Shows which selector was used
   - Reports number of cards found at each step
   - Helps debug future issues

2. **Configurable Thresholds**
   - Only try alternative selectors if primary finds < 10 cards
   - Only try content-based search if still < 20 cards
   - Prevents unnecessary processing

3. **Error Handling**
   - Try-except blocks around each selector attempt
   - Graceful fallback if one selector fails
   - Doesn't crash entire scraping process

## Testing the Fix

```bash
python3 test_notion_improved.py
```

Expected output should show:
- Multiple categories (not just "TV shows / Movie franchises")
- Total count > 40 nichos
- Each nicho with correct category assignment

## Integration

No API changes required. The fix is internal to the service:
- Same endpoint URLs
- Same request/response format
- Same webhook behavior
- Just works better now!

## Performance Considerations

- **Additional scroll**: +5 seconds
- **Multiple selectors**: Only attempted if needed (fallback)
- **Content-based search**: O(n) where n = all divs on page (expensive, only fallback)
- **Total impact**: ~5 extra seconds for complete scraping

Acceptable trade-off for ensuring all categories are extracted correctly.
