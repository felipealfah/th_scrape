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

### 3. Nichos ✅

**URL Exemplo:** `https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA`

**HTML:**
```html
<div class="col">
  <p class="mb-2"><strong>Nicho(s)</strong>:</p>
  <span class="badge badge-soft rounded-pill">
    <a href="https://app.tubehunt.io/long/cruises" class="text-dark">Cruzeiros</a>
  </span>
</div>
```

**Nota:** Diferente de Keywords/Assuntos! O texto está **dentro de um `<a>` tag** dentro do span.

**Seletor CSS (complexo):** Não recomendado para esse caso - use XPath

**XPath:** `//p[contains(., 'Nicho')]/following-sibling::span[@class='badge badge-soft rounded-pill']//a`

**Alternative XPath:** `//p[contains(., 'Nicho')]/following-sibling::span//a`

**Extract Strategy:**
```python
# Usando XPath
niche_elements = page.query_selector_all("//p[contains(., 'Nicho')]/following-sibling::span[@class='badge badge-soft rounded-pill']//a")

niches = []
for elem in niche_elements:
    text = elem.inner_text().strip()
    if text:
        niches.append(text)

return niches
```

**Expected Output:**
```python
["Cruzeiros"]
# ou múltiplos nichos se houver
["Cruzeiros", "Viajería", "Lifestyle"]
```

---

### 4. Views (30 dias) ✅

**URL Exemplo:** `https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA`

**HTML:**
```html
<div class="col">
  <div class="metric text-center">
    <div class="label text-dark">Views (30 dias)</div>
    <div class="value">357.96k</div>
  </div>
</div>
```

**Estrutura:** Label seguido de value no mesmo container `.metric`

**Seletor CSS:** Usar o padrão `div.value` após `div.label`

**XPath:** `//div[@class='label' and contains(., 'Views (30 dias)')]/following-sibling::div[@class='value']`

**Extract Strategy:**
```python
# Usando XPath
views_element = page.query_selector("//div[@class='label' and contains(., 'Views (30 dias)')]/following-sibling::div[@class='value']")

if views_element:
    views_30d = views_element.inner_text().strip()
    return views_30d
else:
    return None
```

**Expected Output:**
```python
"357.96k"
# ou outras variações:
"15000"
"1.5M"
"2.3k"
```

---

### 5. Receita (30 dias) ✅

**URL Exemplo:** `https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA`

**HTML:**
```html
<div class="col">
  <div class="metric text-center">
    <div class="label text-dark">Receita (30 dias)</div>
    <div class="value">$239,00 - $781,00</div>
  </div>
</div>
```

**Estrutura:** Idêntica a Views (30 dias) - label + value no container `.metric`

**Seletor CSS:** Usar o padrão `div.value` após `div.label`

**XPath:** `//div[@class='label' and contains(., 'Receita (30 dias)')]/following-sibling::div[@class='value']`

**Extract Strategy:**
```python
# Usando XPath
revenue_element = page.query_selector("//div[@class='label' and contains(., 'Receita (30 dias)')]/following-sibling::div[@class='value']")

if revenue_element:
    revenue_30d = revenue_element.inner_text().strip()
    return revenue_30d
else:
    return None
```

**Expected Output:**
```python
"$239,00 - $781,00"
# ou outras variações:
"$100 - $500"
"€200 - €800"
"R$ 1000 - R$ 5000"
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

## Summary of All Selectors

| Campo | Status | XPath | Padrão |
|-------|--------|-------|--------|
| **Keywords** | ✅ | `//p[contains(., 'Keywords')]/following-sibling::span[@class='badge badge-soft rounded-pill']` | Badge list (sem link) |
| **Assuntos** | ✅ | `//p[contains(., 'Assuntos')]/following-sibling::span[@class='badge badge-soft rounded-pill']` | Badge list (sem link) |
| **Nichos** | ✅ | `//p[contains(., 'Nicho')]/following-sibling::span[@class='badge badge-soft rounded-pill']//a` | Badge list **com link** |
| **Views (30d)** | ✅ | `//div[@class='label' and contains(., 'Views (30 dias)')]/following-sibling::div[@class='value']` | Metric value |
| **Receita (30d)** | ✅ | `//div[@class='label' and contains(., 'Receita (30 dias)')]/following-sibling::div[@class='value']` | Metric value |

---

## Key Differences to Note

### Badge Lists (Keywords, Assuntos, Nichos)
```
p (header com label)
  ↓
span.badge (múltiplos, siblings)
  ├─ Texto direto (Keywords, Assuntos)
  └─ <a> com texto (Nichos) ← DIFERENÇA!
```

### Metric Values (Views, Receita)
```
div.metric
  ├─ div.label (com texto descritivo)
  └─ div.value (com o valor numérico/monetário)
```

---

## Next Steps

1. ✅ **Keywords:** HTML + Seletor confirmado
2. ✅ **Assuntos:** HTML + Seletor confirmado
3. ✅ **Nichos:** HTML + Seletor confirmado
4. ✅ **Views (30d):** HTML + Seletor confirmado
5. ✅ **Receita (30d):** HTML + Seletor confirmado

---

**Status:** 🎉 **100% MAPEADO - PRONTO PARA IMPLEMENTAÇÃO!**

**Próximo Move:** Aguardando confirmação do usuário para:
1. Fazer `git add` e `git commit` dessas mudanças
2. Começar a codificar o método `scrape_channel_details()` em `app/services/tubehunt.py`
