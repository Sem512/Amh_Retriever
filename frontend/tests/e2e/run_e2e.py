"""End-to-end test suite for the frontend (demo/mock-backend mode).
Run:  npm run build && npx vite preview --port 4173 &  python3 tests/e2e/run_e2e.py
Requires: pip install playwright ; a Chromium binary.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:4173')
CHROMIUM = os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium')
results = []

def record(tc, name, ok, detail=''):
    results.append({'id': tc, 'name': name, 'passed': bool(ok), 'detail': detail})
    print(f"{'PASS' if ok else 'FAIL'}  {tc}  {name}  {detail}")

async def search(pg, q):
    await pg.fill('#q', q); await pg.press('#q', 'Enter')
    await pg.locator('ol li button, :text("ምንም ውጤት")').first.wait_for(timeout=5000)
    await pg.wait_for_timeout(900)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROMIUM)
        pg = await b.new_page(viewport={'width': 1366, 'height': 800})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

        await pg.goto(BASE)
        record('TC-01', 'Home page loads in Amharic with search box and headline',
               await pg.locator('h1').inner_text() == 'ቃሉን ብቻ ሳይሆን ትርጉሙን ፈልጉ' and await pg.locator('#q').is_visible())

        record('TC-02', 'Empty query keeps the Search button disabled',
               await pg.locator('form[role=search] button').is_disabled())

        await search(pg, 'የስራ ግብር መመሪያ')
        n = await pg.locator('ol li button').count()
        record('TC-03', 'Amharic query returns ranked results with count and latency', n == 3 and 'ms' in await pg.locator('form[role=search] p').inner_text(), f'{n} results')

        scores = [int((await pg.locator('ol li button').nth(i).inner_text()).split('%')[0].split()[-1]) for i in range(n)]
        record('TC-04', 'Results are sorted by descending match score', scores == sorted(scores, reverse=True), str(scores))

        hl = pg.locator('section img + div').first
        style = await hl.get_attribute('style')
        record('TC-05', 'Bounding-box highlight overlay is drawn at the normalized coordinates (x=10%, y=18%, w=80%, h=13%)',
               all(s in style for s in ['left: 10%', 'top: 18%', 'width: 80%', 'height: 13%']), style)

        await pg.locator('ol li button').nth(1).click(); await pg.wait_for_timeout(1200)
        pg_label = await pg.locator('section header span').first.inner_text()
        record('TC-06', 'Selecting another result jumps the viewer to that result\'s page', 'ገጽ 2' in pg_label, pg_label)

        prev_dis = await pg.locator('text=ቀዳሚ ውጤት').is_disabled()
        await pg.locator('ol li button').nth(0).click(); await pg.wait_for_timeout(600)
        record('TC-07', 'Previous-result button is disabled on the first result', await pg.locator('text=ቀዳሚ ውጤት').is_disabled())
        await pg.locator('ol li button').nth(2).click(); await pg.wait_for_timeout(600)
        record('TC-08', 'Next-result button is disabled on the last result', await pg.locator('text=ቀጣይ ውጤት').is_disabled())

        await pg.locator('ol li button').nth(0).click(); await pg.wait_for_timeout(1000)
        w0 = (await pg.locator('section img').bounding_box())['width']
        await pg.click('button[aria-label="አጉላ"]'); await pg.wait_for_timeout(300)
        w1 = (await pg.locator('section img').bounding_box())['width']
        await pg.click('button[aria-label="አሳንስ"]'); await pg.click('button[aria-label="አሳንስ"]'); await pg.wait_for_timeout(300)
        w2 = (await pg.locator('section img').bounding_box())['width']
        record('TC-09', 'Zoom in enlarges and zoom out shrinks the page image', w1 > w0 > w2, f'{w2:.0f} < {w0:.0f} < {w1:.0f}px')

        await pg.click('button[aria-label="ቀጣይ ገጽ"]'); await pg.click('button[aria-label="ቀጣይ ገጽ"]'); await pg.wait_for_timeout(800)
        record('TC-10', 'Page navigation stops at the last page (button disabled)', await pg.locator('button[aria-label="ቀጣይ ገጽ"]').is_disabled())

        await search(pg, 'ታክስ')
        titles = await pg.locator('ol li button').all_inner_texts()
        record('TC-11', 'A synonym query (ታክስ) still finds tax passages (semantic match demo)', any('ግብር' in t for t in titles), f'{len(titles)} results')

        await search(pg, 'xyzqq')
        record('TC-12', 'A query with no match shows the empty-state message', await pg.locator('text=ምንም ውጤት አልተገኘም').count() == 1)

        await pg.click('button:has-text("English")')
        record('TC-13', 'Language toggle switches the interface to English', await pg.locator('text=No passages found').count() == 1)
        await pg.click('button:has-text("አማርኛ")')

        await pg.goto(BASE + '/admin'); await pg.wait_for_timeout(400)
        record('TC-14', 'Unauthenticated visit to /admin redirects to the login page', pg.url.endswith('/login'))

        await pg.fill('#u', 'admin'); await pg.fill('#p', 'wrong'); await pg.click('form button'); await pg.wait_for_timeout(700)
        record('TC-15', 'Wrong password shows an inline error and stays on login', await pg.locator('[role=alert]').count() == 1 and pg.url.endswith('/login'))

        await pg.fill('#p', 'admin123'); await pg.click('form button'); await pg.wait_for_url('**/admin'); await pg.wait_for_timeout(600)
        record('TC-16', 'Correct credentials open the admin page and show the document list', await pg.locator('table tbody tr').count() == 3)

        await pg.set_input_files('input[type=file]', {'name': 'gazette.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4'})
        await pg.wait_for_timeout(1500)
        row = pg.locator('table tbody tr', has_text='gazette')
        record('TC-17', 'Uploaded PDF appears in the table with status Processing', await row.count() == 1 and 'በሂደት ላይ' in await row.inner_text())
        await pg.wait_for_timeout(5500)
        record('TC-18', 'Status polling updates the document to Indexed without a page reload', 'ተጠቁሟል' in await row.inner_text())

        await pg.set_input_files('input[type=file]', {'name': 'virus.exe', 'mimeType': 'application/x-msdownload', 'buffer': b'MZ'})
        await pg.wait_for_timeout(500)
        record('TC-19', 'Unsupported file type is rejected with a message', await pg.locator('text=PDF፣ PNG እና JPG ፋይሎች ብቻ').count() == 1)

        pg.once('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await row.locator('button:has-text("ሰርዝ")').click(); await pg.wait_for_timeout(700)
        record('TC-20', 'Deleting a document (after confirmation) removes it from the list', await pg.locator('table tbody tr', has_text='gazette').count() == 0)

        await pg.click('button:has-text("ውጣ")'); await pg.wait_for_timeout(400)
        await pg.goto(BASE + '/admin'); await pg.wait_for_timeout(400)
        record('TC-21', 'After sign-out, admin pages are protected again', pg.url.endswith('/login'))

        m = await b.new_page(viewport={'width': 390, 'height': 800})
        await m.goto(BASE); await m.fill('#q', 'ግብር'); await m.press('#q', 'Enter'); await m.wait_for_selector('ol li button')
        await m.click('ol li button >> nth=0'); await m.wait_for_timeout(1500)
        box = await m.locator('section[aria-label]').bounding_box()
        record('TC-22', 'On a phone, opening a result shows the viewer full-screen', box['width'] >= 385 and box['height'] >= 780, f"{box['width']:.0f}x{box['height']:.0f}")
        await m.click('text=ወደ ውጤቶች ተመለስ'); await m.wait_for_timeout(300)
        record('TC-23', 'On a phone, the Back button returns to the result list', await m.locator('ol li button').first.is_visible())
        no_scroll = await m.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        record('TC-24', 'No horizontal page scrolling at 390 px width', no_scroll)

        # ---- new behaviour: multiple boxes, session expiry, error handling ----
        await pg.goto(BASE); await search(pg, 'የስራ ግብር መመሪያ')
        await pg.locator('ol li button').nth(1).click(); await pg.wait_for_timeout(1200)
        act = pg.locator('section [data-active=true]')
        styles = [await act.nth(i).get_attribute('style') for i in range(await act.count())]
        ok = len(styles) == 2 and 'top: 28%' in styles[0] and 'top: 32.5%' in styles[1] and all('left: 10%' in x for x in styles)
        record('TC-25', 'A result with a bboxes array draws one highlight box per entry (2 boxes for a two-line passage)', ok, f'{len(styles)} boxes')

        await pg.locator('ol li button').nth(0).click(); await pg.wait_for_timeout(1000)
        record('TC-26', 'A result with only a single bbox still draws exactly one highlight box (fallback)',
               await pg.locator('section [data-active=true]').count() == 1)

        async def admin_login():
            await pg.goto(BASE + '/login'); await pg.fill('#u', 'admin'); await pg.fill('#p', 'admin123')
            await pg.click('form button'); await pg.wait_for_url('**/admin'); await pg.wait_for_timeout(500)

        await admin_login()
        await pg.evaluate("sessionStorage.setItem('token', 'expired-token')")
        await pg.reload(); await pg.wait_for_url('**/login'); await pg.wait_for_timeout(300)
        notice = await pg.locator('[role=status]').inner_text()
        cleared = await pg.evaluate("sessionStorage.getItem('token') === null && sessionStorage.getItem('user') === null")
        record('TC-27', 'An expired or invalid token (401) clears the session and redirects to login with a notice, instead of showing "no documents"',
               'ክፍለ ጊዜዎ አብቅቷል' in notice and cleared and await pg.locator('text=ምንም ሰነድ').count() == 0, notice[:40])

        await admin_login()
        await pg.set_input_files('input[type=file]', {'name': 'busy.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4'})
        await pg.wait_for_timeout(1300)
        pg.once('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.locator('table tbody tr', has_text='busy').locator('button:has-text("ሰርዝ")').click(); await pg.wait_for_timeout(700)
        alert = await pg.locator('main [role=alert]').first.inner_text()
        record('TC-28', 'A failed delete shows the backend message and keeps the document in the list',
               'cannot be deleted yet' in alert and await pg.locator('table tbody tr', has_text='busy').count() == 1, alert[:80])

        await pg.set_input_files('input[type=file]', {'name': 'fail-scan.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4'})
        await pg.wait_for_timeout(1300)
        up = await pg.locator('ul[aria-live] li', has_text='fail-scan.pdf').inner_text()
        record('TC-29', "A failed upload shows the backend's detail message, not the HTTP status text",
               'OCR service unavailable: could not read page 1' in up, up.replace('\n', ' ')[:80])

        await pg.set_input_files('input[type=file]', [
            {'name': 'dup.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-1.4'},
            {'name': 'dup.pdf', 'mimeType': 'application/pdf', 'buffer': b''}])
        await pg.wait_for_timeout(2200)
        rows = pg.locator('ul[aria-live] li', has_text='dup.pdf')
        texts = [await rows.nth(i).inner_text() for i in range(await rows.count())]
        record('TC-30', 'Two uploads with the same file name get separate rows with independent results',
               len(texts) == 2 and sum('empty' in t for t in texts) == 1 and sum('100%' in t for t in texts) == 1,
               ' | '.join(t.replace('\n', ' ') for t in texts)[:100])

        record('TC-31', 'No JavaScript or console errors during the whole session', len(errors) == 0, '; '.join(errors)[:120])
        await b.close()

    passed = sum(r['passed'] for r in results)
    print(f'\n{passed}/{len(results)} passed')
    json.dump(results, open(os.path.join(os.path.dirname(__file__), 'e2e_results.json'), 'w'), ensure_ascii=False, indent=1)
    sys.exit(0 if passed == len(results) else 1)

asyncio.run(main())
