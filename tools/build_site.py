"""Builds the standalone website (index.html) from the Claude artifact version (artifact/index.html).

The site swaps the artifact's built-in storage for Firebase (no accounts: a private family link),
names phones locally for the feed, and saves PDFs through the phone's share sheet.
"""
import re, sys
src = open('artifact/index.html', encoding='utf-8').read()
s = src

def rep(a, b, count=1):
    global s
    n = s.count(a)
    if n != count:
        sys.exit(f'expected {count} match(es), found {n}: {a[:100]!r}')
    s = s.replace(a, b)

# ---------- document shell ----------
rep('<meta charset="utf-8">\n<title>Little Sprouts</title>\n', '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Little Sprouts</title>
<meta name="description" content="Family learning games for little ones: colors, animals, shapes, counting, letters and more.">
<meta name="theme-color" content="#2F9E57">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Little Sprouts">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
''')
rep('<style>\n/* Layout:', '''<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; -webkit-text-size-adjust: 100%; }
img { max-width: 100%; }
[hidden] { display: none !important; }
/* Layout:''')
rep('</style>\n\n<main class="app" id="app">', '</style>\n</head>\n<body>\n<main class="app" id="app">')
s = s.rstrip() + '\n</body>\n</html>\n'
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/', '''<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="config.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/''')

# ---------- family link + phone name ----------
rep("let db = null, user = null, myId = null;", r"""let db = null, user = null, myId = null;
const FAMILY_KEY = 'little-sprouts-family', PHONE_KEY = 'little-sprouts-phone';
let FAMILY = null;
function getFamily() {
  const q = new URLSearchParams(location.search).get('family');
  if (q && /^[a-z0-9]{16,40}$/.test(q)) { try { localStorage.setItem(FAMILY_KEY, q); } catch (e) {} return q; }
  try { const v = localStorage.getItem(FAMILY_KEY); if (v) { history.replaceState(null, '', '?family=' + v); return v; } } catch (e) {}
  return null;
}
const familyLink = () => location.origin + location.pathname + '?family=' + FAMILY;
function startFamily() {
  const a = new Uint8Array(16); crypto.getRandomValues(a);
  const id = Array.from(a, b => (b % 36).toString(36)).join('') + Date.now().toString(36).slice(-4);
  try { localStorage.setItem(FAMILY_KEY, id); } catch (e) {}
  location.replace(location.pathname + '?family=' + id);
}
const phoneName = () => { try { return (localStorage.getItem(PHONE_KEY) || '').trim(); } catch (e) { return ''; } };""")

rep("""  if (S.readOnly) wrap.append(h('div', { class: 'notice' }, 'You can watch the family feed. Ask the owner to share this page with you as an editor so you can add learners and save stars.'));
  else if (!S.loading && !S.live) wrap.append(h('div', { class: 'notice' }, 'Playing on this phone only. Open the shared link from Claude to see the whole family live.'));""",
"""  if (S.readOnly) wrap.append(h('div', { class: 'notice' }, 'Changes could not be saved. Check the internet connection, then reopen the app.'));
  else if (S.needFamily) wrap.append(h('section', { class: 'today' },
    h('h2', {}, 'Set up your family'),
    h('p', { class: 'thint' }, 'Start your family on this phone, then send the family link to everyone who helps. Anyone with the link can add children, play, and see the stars. Nobody needs an account.'),
    h('div', { class: 'actions', style: 'justify-content:flex-start' }, h('button', { class: 'btn', type: 'button', onclick: startFamily }, 'Start our family')),
    h('p', { class: 'thint' }, 'Already have a family link? Open that link on this phone instead.')));
  else if (!S.loading && !S.live) wrap.append(h('div', { class: 'notice' }, window.SPROUT_FIREBASE ? 'Could not reach the family. Playing on this phone only for now.' : 'Family sharing is not switched on yet. Lessons work, but children and stars stay on this phone.'));""")

# family panel above the voice settings
rep("  wrap.append(voicePanel());", "  if (S.live) wrap.append(familyPanel());\n  wrap.append(voicePanel());")
rep("function voicePanel() {", r"""function familyPanel() {
  const link = familyLink();
  const name = h('input', { id: 'phone-name', maxlength: '20', autocomplete: 'off', placeholder: 'Mom, Grandma, Sitter…', value: phoneName(),
    onchange: e => { try { localStorage.setItem(PHONE_KEY, e.target.value.trim()); } catch (x) {} render(); } });
  const linkBox = h('div', { class: 'flink' }, link);
  const status = h('span', { class: 'thint' });
  const share = h('button', { class: 'btn', type: 'button', onclick: async () => {
      try { if (navigator.share) { await navigator.share({ title: 'Little Sprouts', text: 'Join our family on Little Sprouts:', url: link }); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
      try { await navigator.clipboard.writeText(link); status.textContent = 'Link copied.'; } catch (e) { status.textContent = 'Press and hold the link to copy it.'; }
    } }, 'Send family link');
  return h('section', { class: 'voice' },
    h('div', { class: 'sec-head' }, h('h2', {}, 'Family'), h('span', {}, 'No accounts needed')),
    h('div', { class: 'vrow' },
      h('label', { class: 'field', for: 'phone-name' }, 'Name for this phone (shows in the feed)', name),
      h('div', { class: 'field' }, 'Family link', linkBox),
      h('p', { class: 'thint', style: 'margin:0' }, 'Send this link to grandparents, sitters and anyone who helps. Keep it private: anyone with it can see and change your family.'),
      h('div', { class: 'actions', style: 'justify-content:flex-start;align-items:center;flex-wrap:wrap' }, share, status)));
}

function voicePanel() {""")
rep(".field select {", ".flink { font: 600 .85rem/1.4 ui-monospace, Menlo, monospace; background: var(--bg); border-radius: 12px; padding: 10px 12px; overflow-wrap: anywhere; user-select: all; -webkit-user-select: all; }\n.field select {")

# ---------- feed names come from each phone's name ----------
rep("""  let names = {};
  const ids = [...new Set(items.map(f => f.by).filter(Boolean))];
  if (user && ids.length) { try { names = await user.profiles(ids); } catch (e) {} }
""", "")
rep("    const who = f.by && names[f.by] ? (names[f.by].isMe ? 'you' : names[f.by].name || 'a grown-up') : null;",
    "    const who = f.by && f.by === myId ? 'you' : (f.byName || null);")
rep("    d = { ...d, ts: Date.now(), by: myId || null };", "    d = { ...d, ts: Date.now(), by: myId || null, byName: phoneName() || null };")
rep("  if (e && e.code === 'invalid_argument') { S.readOnly = true; render(); }",
    "  if (e && (e.code === 'invalid_argument' || e.code === 'permission-denied')) { S.readOnly = true; render(); }")

# ---------- saving the PDF: the phone's share sheet (has Print), else a normal download ----------
rep("let downloads = null;", r"""async function saveFile(blob, filename) {
  const file = new File([blob], filename, { type: 'application/pdf' });
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try { await navigator.share({ files: [file], title: filename }); return; }
    catch (e) { if (e && e.name === 'AbortError') throw { code: 'declined' }; }
  }
  const url = URL.createObjectURL(blob), a = h('a', { href: url, download: filename });
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 60000);
}
const downloads = { save: ({ filename, data }) => saveFile(data, filename) };
// The PDF is built ahead of time, so tapping Print opens the share sheet right away (phones only allow it straight after a tap).
const pdfCache = new Map();
function packPdf(k) {
  const id = todayKey() + k.id + k.age + k.name;
  if (!pdfCache.has(id)) {
    const entry = { blob: null };
    entry.promise = packPages(k).then(pages => {
      const { jsPDF } = window.jspdf, pdf = new jsPDF({ unit: 'in', format: 'letter' });
      pages.forEach((cv, i) => { if (i) pdf.addPage('letter'); pdf.addImage(cv.toDataURL('image/jpeg', 0.9), 'JPEG', 0, 0, 8.5, 11); });
      return (entry.blob = pdf.output('blob'));
    });
    pdfCache.set(id, entry);
  }
  return pdfCache.get(id);
}""")
start = s.index("async function savePack(k, btn) {"); end = s.index("async function paperDone(", start)
s = s[:start] + r"""async function savePack(k, btn) {
  const label = btn.textContent, entry = packPdf(k);
  if (!entry.blob) {
    btn.disabled = true; btn.textContent = 'Getting pages ready…';
    try { await entry.promise; } catch (e) {}
    btn.disabled = false; btn.textContent = entry.blob ? 'Ready. Tap again to print' : label;
    return;
  }
  try {
    const safe = (k.name || 'Lesson').replace(/[^\p{L}\p{N} _-]/gu, '').trim() || 'Lesson';
    await downloads.save({ filename: `${safe} lessons ${todayKey()}.pdf`, data: entry.blob });
    btn.textContent = label;
  } catch (e) {
    btn.textContent = e && e.code === 'declined' ? label : 'Could not open it. Use See pages instead.';
    setTimeout(() => { if (btn.isConnected) btn.textContent = label; }, 5000);
  }
}
""" + s[end:]
rep("  if (canSave) actions.prepend(h('button', { class: 'btn', type: 'button', onclick: e => savePack(k, e.currentTarget) }, `🖨 Print today's lessons`));",
    "  if (canSave) { actions.prepend(h('button', { class: 'btn', type: 'button', onclick: e => savePack(k, e.currentTarget) }, `🖨 Print today's lessons`)); setTimeout(() => packPdf(k), 400); }")
rep("Print all ${n} pages to do today's lessons without the phone: the plan, one page per lesson, and a practice sheet. Save the PDF, open it, then tap Share and Print.",
    "Print all ${n} pages to do today's lessons without the phone: the plan, one page per lesson, and a practice sheet. Tap Print today's lessons, then choose Print.")

# ---------- connection: Firebase with a private family link ----------
start = s.index("async function connect() {"); end = s.index("connect();\n})();", start)
s = s[:start] + r"""async function connect() {
  const cfg = window.SPROUT_FIREBASE;
  if (!cfg || !window.firebase) { S.loading = false; render(); return; }
  FAMILY = getFamily();
  if (!FAMILY) { S.loading = false; S.needFamily = true; render(); return; }
  try {
    firebase.initializeApp(cfg);
    const fs = firebase.firestore();
    try { await fs.enablePersistence({ synchronizeTabs: true }); } catch (e) {}
    const cred = await firebase.auth().signInAnonymously();
    myId = cred.user.uid;
    const root = fs.collection('families').doc(FAMILY);
    // Same small interface the lessons already use; updates merge into nested fields like the original store.
    const wrapDoc = ref => ({
      id: ref.id,
      get: () => ref.get(),
      set: d => ref.set(d),
      update: d => ref.set(d, { merge: true }),
      delete: () => ref.delete(),
      onSnapshot: (next, err) => ref.onSnapshot(next, err)
    });
    db = {
      collection: p => root.collection(p),
      doc: p => { const [c, d] = p.split('/'); return wrapDoc(root.collection(c).doc(d)); }
    };
    S.live = true; S.kids = []; S.feed = [];
    let first = 0;
    const ready = () => { if (++first === 2) { S.loading = false; } render(); };
    root.collection('kids').onSnapshot(s => { S.kids = s.docs.map(x => ({ id: x.id, ...x.data() })); ready(); }, () => { S.loading = false; render(); });
    db.doc('settings/voice').onSnapshot(snap => {
      const v = snap.exists ? snap.data() : null;
      wordReview = { approve: (v && v.approve) || {}, reject: (v && v.reject) || {} };
      if (S.view === 'home' && !S.sheet) render();
    }, () => {});
    root.collection('feed').orderBy('ts', 'desc').limit(40).onSnapshot(s => { S.feed = s.docs.map(x => ({ id: x.id, ...x.data() })); ready(); }, () => { S.loading = false; render(); });
  } catch (e) { S.live = false; S.loading = false; render(); }
}
""" + s[end:]
rep("const S = { kids: [], feed: [], live: false, loading: true,", "const S = { kids: [], feed: [], live: false, loading: true, needFamily: false,")

for bad in ('window.claude', 'claude.use'):
    if bad in s: sys.exit('leftover platform reference: ' + bad)
open('index.html', 'w', encoding='utf-8').write(s)
print('index.html built,', len(s), 'bytes')
