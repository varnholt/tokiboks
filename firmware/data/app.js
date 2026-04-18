// Tab switching
const tabs   = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');

tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(b => b.classList.remove('active'));
  panels.forEach(p => p.classList.remove('active'));
  t.classList.add('active');
  const panel = document.getElementById('tab-' + t.dataset.tab);
  panel.classList.add('active');
  if (t.dataset.tab === 'map') {
    document.querySelector('#map-body tr.hi')
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}));

// API helpers
const get  = path => fetch(path).then(r => { if (!r.ok) throw r.status; return r.json(); });
const post = (path, data) => fetch(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
}).then(r => { if (!r.ok) throw r.status; return r.json(); });

// Toast
let _tt;
const toast = (msg, ok = true) => {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'on' + (ok ? '' : ' err');
  clearTimeout(_tt);
  _tt = setTimeout(() => el.classList.remove('on'), 3000);
};

// Credentials
get('/api/credentials').then(d => {
  const f = document.getElementById('form-creds');
  for (const [k, v] of Object.entries(d)) if (f.elements[k]) f.elements[k].value = v;
}).catch(e => console.warn('credentials load failed', e));

document.getElementById('form-creds').addEventListener('submit', async e => {
  e.preventDefault();
  const f = e.target;
  try {
    await post('/api/credentials', {
      wifi_ssid:      f.elements.wifi_ssid.value.trim(),
      wifi_password:  f.elements.wifi_password.value,
      admin_username: f.elements.admin_username.value.trim(),
      admin_password: f.elements.admin_password.value,
    });
    toast('Credentials saved.');
  } catch { toast('Save failed.', false); }
});

document.getElementById('btn-restart').addEventListener('click', async () => {
  if (!confirm('Restart the device now?')) return;
  try {
    await fetch('/api/restart', { method: 'POST' });
    toast('Device is restarting\u2026');
  } catch { toast('Restart failed.', false); }
});

// Server config
get('/api/server-config').then(d => {
  const f = document.getElementById('form-srv');
  for (const [k, v] of Object.entries(d)) if (f.elements[k]) f.elements[k].value = v;
}).catch(e => console.warn('server-config load failed', e));

document.getElementById('form-srv').addEventListener('submit', async e => {
  e.preventDefault();
  const f = e.target;
  try {
    await post('/api/server-config', {
      server_host: f.elements.server_host.value.trim(),
      server_port: parseInt(f.elements.server_port.value, 10),
    });
    toast('Server config saved.');
  } catch { toast('Save failed.', false); }
});

// Music mapping
let entries = [];

get('/api/music-mapping').then(d => {
  const raw = d.entries ?? [];
  entries = Array.from({ length: 100 }, (_, i) => raw[i] ?? { rfid: '', label: '' });
  renderMap();
}).catch(e => console.warn('mapping load failed', e));

const esc = s => String(s)
  .replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');

function renderMap() {
  const frag = document.createDocumentFragment();
  entries.forEach((e, i) => {
    const tr = document.createElement('tr');
    tr.dataset.i = i;
    tr.innerHTML =
      `<td class="n">${i + 1}</td>` +
      `<td><input type="text" class="rfid" value="${esc(e.rfid)}" placeholder="RFID" spellcheck="false"></td>` +
      `<td><input type="text" value="${esc(e.label)}" placeholder="path or URL"></td>`;
    frag.appendChild(tr);
  });
  const body = document.getElementById('map-body');
  body.innerHTML = '';
  body.appendChild(frag);
}

function collect() {
  document.querySelectorAll('#map-body tr').forEach((tr, i) => {
    const [rfidIn, labelIn] = tr.querySelectorAll('input');
    entries[i] = { rfid: rfidIn.value.trim(), label: labelIn.value.trim() };
  });
}

document.getElementById('btn-save-map').addEventListener('click', async () => {
  collect();
  try {
    await post('/api/music-mapping', { entries });
    toast('Mapping saved.');
  } catch { toast('Save failed.', false); }
});

// RFID highlight / auto-fill
let lastUid = '';

function highlight(i) {
  document.querySelectorAll('#map-body tr').forEach(r => r.classList.remove('hi'));
  const tr = document.querySelector(`#map-body tr[data-i="${i}"]`);
  if (!tr) return;
  tr.classList.add('hi');
  if (document.getElementById('tab-map').classList.contains('active'))
    tr.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function onScan(uid) {
  collect();
  const i = entries.findIndex(e => e.rfid.toUpperCase() === uid.toUpperCase());
  if (i >= 0) { highlight(i); return; }
  const empty = entries.findIndex(e => !e.rfid.trim());
  if (empty >= 0) { entries[empty].rfid = uid; renderMap(); highlight(empty); }
}

// Poll last scanned RFID every 2 s
setInterval(() =>
  get('/api/last-rfid').then(d => {
    if (d.uid && d.uid !== lastUid) { lastUid = d.uid; onScan(d.uid); }
  }).catch(() => {}),
2000);
