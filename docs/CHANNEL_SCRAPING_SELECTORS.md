# Channel Scraping - HTML Selectors Reference

**Última Atualização:** 2026-01-23
**Status:** Em progresso (2 de 5 campos mapeados)

---

## Mapped Selectors (Pronto para usar)

### 1. Keywords ✅

**URL Exemplo:** `https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA`

**HTML:**
```html
<div class="col">
  <p class="mb-2"><strong>Keywords</strong> do canal:</p>
  <span class="badge badge-soft rounded-pill">cruceros 2025<span class="opacity-0">,</span></span>
  <span class="badge badge-soft rounded-pill">viajar en crucero<span class="opacity-0">,</span></span>
  ...
</div>
```

**CSS Selector:** `span.badge.badge-soft.rounded-pill`

**XPath:** `//p[contains(., 'Keywords')]/following-sibling::span[@class='badge badge-soft rounded-pill']`

**Extract Strategy:**
```python
# Encontrar o p com "Keywords"
p_element = page.query_selector("p:has-text('Keywords')")  # ou usar XPath

# Se usar XPath:
keyword_elements = page.query_selector_all("//p[contains(., 'Keywords')]/following-sibling::span[@class='badge badge-soft rounded-pill']")

# Extrair texto de cada span
keywords = []
for elem in keyword_elements:
    text = elem.inner_text().strip()
    if text:  # ignorar vazios
        keywords.append(text)

return keywords
```

**Expected Output:**
```python
[
  "cruceros 2025",
  "viajar en crucero",
  "consejos para cruceros",
  "mejores cruceros del mundo",
  ...
]
```

---

### 2. Assuntos ✅

**URL Exemplo:** `https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA`

**HTML:**
```html
<div class="col">
  <p class="mb-2"><strong>Assuntos</strong> (identificados automaticamente):</p>
  <span class="badge badge-soft rounded-pill">Tourism</span>
  <span class="badge badge-soft rounded-pill">Food</span>
  <span class="badge badge-soft rounded-pill">Lifestyle (sociology)</span>
  <span class="badge badge-soft rounded-pill">Society</span>
</div>
```

**CSS Selector:** `span.badge.badge-soft.rounded-pill`

**XPath:** `//p[contains(., 'Assuntos')]/following-sibling::span[@class='badge badge-soft rounded-pill']`

**Extract Strategy:**
```python
# Encontrar o p com "Assuntos"
# Se usar XPath:
subject_elements = page.query_selector_all("//p[contains(., 'Assuntos')]/following-sibling::span[@class='badge badge-soft rounded-pill']")

# Extrair texto
subjects = []
for elem in subject_elements:
    text = elem.inner_text().strip()
    if text:
        subjects.append(text)

return subjects
```

**Expected Output:**
```python
[
  "Tourism",
  "Food",
  "Lifestyle (sociology)",
  "Society"
]
```

---

## Pending Selectors (Aguardando HTML)

### 3. Nichos ⏳

**Expected Structure:** Similar a Keywords/Assuntos

**Placeholder for HTML:**
```
[Aguardando HTML do usuário...]
```

---

### 4. Views (30 dias) ⏳

**Expected Format:** Numeric string (ex: "15000", "15k", "1.5M")

**Placeholder for HTML:**
```
[Aguardando HTML do usuário...]
```

---

### 5. Receita (30 dias) ⏳

**Expected Format:** Monetary string (ex: "$450.00", "€350", "R$ 1200")

**Placeholder for HTML:**
```
[Aguardando HTML do usuário...]
```

---

## Implementation Notes

### General Approach for Extracting Badges

Quando o padrão é `<div class="col">` com um `<p>` descritivo seguido por `<span class="badge">` elementos:

1. **Use XPath com `contains()` para encontrar o header:**
   ```xpath
   //p[contains(., 'LABEL_TEXT')]/following-sibling::span[@class='badge badge-soft rounded-pill']
   ```

2. **Alternative: CSS com seletor contextual:**
   ```javascript
   // Mais genérico - pega o container div.col e extrai spans
   // Mas precisa de lógica para diferenciar qual seção é qual
   ```

3. **Python/Playwright Implementation Pattern:**
   ```python
   def extract_badge_list(page, label_text):
       """
       Extrai lista de badges baseado no label (ex: 'Keywords', 'Assuntos', etc)
       """
       xpath = f"//p[contains(., '{label_text}')]/following-sibling::span[@class='badge badge-soft rounded-pill']"
       elements = page.query_selector_all(xpath)

       items = []
       for elem in elements:
           text = elem.inner_text().strip()
           if text:
               items.append(text)

       return items
   ```

### Text Extraction Tips

- **Keywords:** Cada span contém texto + inner span com `opacity-0` (vírgula invisível). Use `inner_text()` que pega todo o texto.
- **Assuntos:** Spans mais simples, sem elementos internos. Direto com `inner_text()`.
- **Nichos:** A confirmar quando HTML for recebido.

---

## Next Steps

1. ✅ **Keywords:** Seletor CSS confirmado
2. ✅ **Assuntos:** Seletor CSS confirmado
3. ⏳ **Aguardando:** Nichos HTML
4. ⏳ **Aguardando:** Views (30d) HTML
5. ⏳ **Aguardando:** Revenue (30d) HTML

Assim que o usuário enviar os HTMLs restantes, seções serão atualizadas com seletores finais.

---

**Status:** Ready for implementation of Keywords + Subjects
**Next Move:** Codificar `scrape_channel_details()` com esses 2 campos
