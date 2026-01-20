# Testing Instructions - Notion Scraping Fixes

## Quick Test (Local)

### 1. Run the improved test script
```bash
python3 test_notion_improved.py
```

This script will:
- ✅ Connect to the Notion page
- ✅ Wait for full page load with scroll
- ✅ Try multiple card detection strategies
- ✅ Extract cards from all categories
- ✅ Display results grouped by category

Expected output:
```
Encontradas 5 seções de categoria (h3s)
  - TV shows / Movie franchises
  - Aviation
  - Cars
  - Nostalgia
  - Other

TV shows / Movie franchises: 9 nichos
Aviation: 8 nichos
Cars: 12 nichos
Nostalgia: 10 nichos
Other: 8 nichos

✅ Total: 5 categorias, 47 nichos extraídos
```

### 2. Verify extraction correctness

Check the output for:
- [ ] **At least 4+ different categories** (not just "TV shows")
- [ ] **Total count > 40 nichos** (not just ~9)
- [ ] **Each nicho has correct category assigned**
- [ ] **No errors in logs**

---

## API Test (Docker)

### 1. Start the application
```bash
docker-compose up -d
```

### 2. Call the Notion scraping endpoint
```bash
curl -X POST http://localhost:8000/api/v1/notion/scrape-nichos/start \
  -H "Content-Type: application/json" \
  -d '{
    "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
    "wait_time": 25
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job enfileirado com sucesso",
  "created_at": "2026-01-20T21:00:00"
}
```

### 3. Poll for results
```bash
curl http://localhost:8000/api/v1/notion/scrape-nichos/result/550e8400-e29b-41d4-a716-446655440000
```

Expected response after job completes:
```json
{
  "success": true,
  "nichos": [
    {
      "name": "Game of Thrones",
      "category": "TV shows / Movie franchises",
      "image_url": "https://...",
      "rpm": "$5000",
      "sub_niche": "Movies",
      "data": "N/A",
      "place": "N/A",
      "url": "https://..."
    },
    {
      "name": "Airplane Documentary",
      "category": "Aviation",
      "image_url": "https://...",
      "rpm": "$3000",
      "sub_niche": "Documentary",
      "data": "N/A",
      "place": "N/A",
      "url": "https://..."
    },
    ...
  ],
  "total_nichos": 47,
  "error": null
}
```

### 4. Verify webhook integration (optional)
If using n8n or webhook service:
```bash
curl -X POST http://localhost:8000/api/v1/notion/scrape-nichos/start \
  -H "Content-Type: application/json" \
  -d '{
    "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
    "wait_time": 25,
    "webhook_url": "https://your-webhook-url.com/callback"
  }'
```

Check your webhook endpoint for callback with all extracted nichos.

---

## Checking the Logs

### Docker logs
```bash
docker-compose logs scraper-api -f
```

Look for:
```
INFO - Seletor 1 (.notion-collection-item): encontrados 12 cards
INFO - Seletor 2 (div[data-block-id]): encontrados 35 cards
INFO - Seletor 3: encontrados 47 elementos únicos
INFO - Encontradas 5 seções de categoria (h3s)
INFO - Processando card 1/47 (Categoria: TV shows / Movie franchises)...
   ✅ Card extraído: Game of Thrones | RPM: $5000
...
INFO - ✅ 47 nichos extraídos com sucesso
```

### Specific details to verify

1. **Multiple selectors being used**
   ```
   Seletor 1: found X cards
   Seletor 2: found Y cards  ← Multiple numbers = good!
   Seletor 3: found Z cards
   ```

2. **Multiple categories detected**
   ```
   Encontradas 5 seções de categoria (h3s)  ← Should be > 1
     - TV shows / Movie franchises
     - Aviation                              ← Multiple categories = good!
     - Cars
     - Nostalgia
     - Other
   ```

3. **Cards from different categories**
   ```
   Processando card 1/47 (Categoria: TV shows / Movie franchises)...
   Processando card 10/47 (Categoria: Aviation)...  ← Category changed = good!
   Processando card 20/47 (Categoria: Cars)...
   Processando card 35/47 (Categoria: Nostalgia)...
   ```

4. **High total count**
   ```
   ✅ 47 nichos extraídos com sucesso  ← Should be >> 9
   ```

---

## Troubleshooting

### Problem: Still only 9 cards extracted
**Solution:**
- Check if `wait_time` is enough (try increasing to 30-40)
- Verify page scrolling is working (check logs for "Scroll concluído")
- Try different browser (Chromium vs Firefox)

### Problem: Wrong category assignments
**Solution:**
- Check logs show all 5 h3s detected
- Verify card positions are increasing (each card has `card_position` > previous)
- Check h3 positions are in order (each h3 position > previous)

### Problem: Timeout errors
**Solution:**
- Increase `wait_time` parameter (default 20, try 30)
- Increase Playwright timeout (line 159 in notion.py: `timeout=120000`)
- Check network connectivity to notion.site

### Problem: "Empty nichos" response
**Solution:**
- Wait longer for job completion (webhook may be slow)
- Check if job failed: `GET /api/v1/notion/scrape-nichos/result/{job_id}`
- Look for error message in response

---

## Comparison: Before vs After

### Before Fix
```
Only 9 nichos extracted
All from "TV shows / Movie franchises"
Aviation, Cars, Nostalgia categories: EMPTY
```

### After Fix
```
47+ nichos extracted
Distributed across all categories:
- TV shows: 9
- Aviation: 8
- Cars: 12
- Nostalgia: 10
- Other: 8
```

---

## Validation Checklist

When testing, ensure ALL of these pass:

- [ ] Test script runs without errors
- [ ] At least 40+ nichos extracted (not ~9)
- [ ] At least 4 different categories detected
- [ ] Each nicho has correct category assigned
- [ ] Logs show multiple selectors being tried
- [ ] No timeout errors
- [ ] No memory leaks (process stable)
- [ ] Webhook callbacks work (if enabled)
- [ ] Results are consistent across runs

---

## Expected Timeline

| Step | Duration |
|------|----------|
| Page load | ~3s |
| Wait time | 20-25s |
| Scroll | ~8s |
| Card detection | ~2s |
| Card extraction | ~10-15s |
| **Total** | **~45-55s** |

If significantly slower, there may be network/system issues.

---

## Next Steps

1. ✅ Run `test_notion_improved.py` locally
2. ✅ Verify all categories are extracted
3. ✅ Test API endpoint with Docker
4. ✅ Monitor logs for any issues
5. ✅ Deploy to production (EasyPanel)
6. ✅ Verify webhook callbacks work
7. ✅ Monitor for 24 hours to ensure stability

All good? The fix is complete and working! 🎉
