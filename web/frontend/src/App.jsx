import React, { useState, useEffect, useRef } from 'react'
import { IcGrid, IcFile, IcSparkle, IcCpu, IcRefresh, IcSend, IcImage, IcClipboard } from './Icons'

const api = (p, opts) => fetch(p, opts).then(r => r.json())

// account_id = sha256(licencia)[:16], identico al contrato (seccion 0).
async function accountIdFor(key) {
  const data = new TextEncoder().encode((key || '').trim())
  const buf = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 16)
}

export default function App() {
  const [tab, setTab] = useState('productos')
  const [health, setHealth] = useState({})
  const [session, setSession] = useState({})
  const [items, setItems] = useState([])          // {page, filename, url, info, selected}
  const [cfg, setCfg] = useState(null)
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(null)  // {done,total,ok,fail}
  const [logLines, setLogLines] = useState([])
  const [history, setHistory] = useState({ summary: {}, records: [] })
  const [drag, setDrag] = useState(false)
  const [licenseKey, setLicenseKey] = useState(() => localStorage.getItem('eleka_license') || '')
  const [accountId, setAccountId] = useState('')
  const [agentOnline, setAgentOnline] = useState(false)
  const wsRef = useRef(null)
  const logRef = useRef(null)

  const refreshStatus = async () => {
    setHealth(await api('/api/health'))
    setSession(await api('/api/session'))
  }
  useEffect(() => {
    refreshStatus()
    api('/api/config').then(setCfg)
    const t = setInterval(refreshStatus, 4000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight }, [logLines])

  const log = (m) => setLogLines(l => [...l, m])

  // ---------- PDF ----------
  const uploadPdf = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setBusy(true); log(`Subiendo ${file.name}...`)
    const fd = new FormData(); fd.append('file', file)
    try {
      const res = await fetch('/api/upload-pdf', { method: 'POST', body: fd }).then(r => r.json())
      setItems((res.items || []).map(it => ({ ...it, info: null, selected: false })))
      log(`Extraidas ${res.count} paginas`)
    } catch (err) { log('Error subiendo PDF: ' + err) }
    setBusy(false)
  }

  // ---------- Imagenes (subir / pegar / arrastrar) ----------
  const addImages = async (fileList) => {
    const files = Array.from(fileList || []).filter(f => f.type && f.type.startsWith('image/'))
    if (!files.length) return
    setBusy(true); log(`Subiendo ${files.length} foto(s)...`)
    const fd = new FormData()
    files.forEach(f => fd.append('files', f))
    try {
      const res = await fetch('/api/upload-images', { method: 'POST', body: fd }).then(r => r.json())
      if (res.detail) { log('Error: ' + res.detail) }
      else {
        setItems(arr => {
          const base = arr.length
          const add = (res.items || []).map((it, i) => ({ ...it, page: base + i + 1, info: null, selected: false }))
          return [...arr, ...add]
        })
        log(`Agregadas ${res.count} foto(s)`)
      }
    } catch (e) { log('Error subiendo fotos: ' + e) }
    setBusy(false)
  }

  // pegar imagenes con Ctrl+V en cualquier parte de la app
  useEffect(() => {
    const onPaste = (e) => {
      const items = e.clipboardData && e.clipboardData.items
      if (!items) return
      const imgs = []
      for (const it of items) {
        if (it.type && it.type.startsWith('image/')) { const f = it.getAsFile(); if (f) imgs.push(f) }
      }
      if (imgs.length) { e.preventDefault(); addImages(imgs) }
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [])

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false)
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) addImages(e.dataTransfer.files)
  }

  // ---------- IA ----------
  const analyze = async (idx, force = false) => {
    const it = items[idx]
    setItems(arr => arr.map((x, i) => i === idx ? { ...x, analyzing: true } : x))
    try {
      const info = await api('/api/analyze', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: it.filename, force }),
      })
      if (info.detail) { log('IA: ' + info.detail); }
      setItems(arr => arr.map((x, i) => i === idx ? { ...x, analyzing: false, selected: true, info: {
        title: info.title || '', price: info.price || '', description: info.description || '', tags: info.tags || [],
      } } : x))
    } catch (e) { log('Error IA: ' + e); setItems(arr => arr.map((x, i) => i === idx ? { ...x, analyzing: false } : x)) }
  }

  const analyzeAll = async () => {
    for (let i = 0; i < items.length; i++) { if (!items[i].info) await analyze(i) }
  }

  const editInfo = (idx, field, value) =>
    setItems(arr => arr.map((x, i) => i === idx ? { ...x, info: { ...x.info, [field]: value } } : x))

  const toggle = (idx) => setItems(arr => arr.map((x, i) => i === idx ? { ...x, selected: !x.selected } : x))

  // ---------- Demo ----------
  const svgPlaceholder = (txt) => {
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200'><rect width='100%' height='100%' fill='#0c1326'/><rect x='8' y='8' width='284' height='184' rx='10' fill='none' stroke='#243152'/><text x='50%' y='50%' fill='#00d4ff' font-family='Segoe UI' font-size='16' text-anchor='middle' dominant-baseline='middle'>${txt}</text></svg>`
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
  }
  const demoSamples = [
    { title: 'Audifonos Bluetooth TWS Pro', price: '17', description: 'GENTE LLEGARON LOS AUDIFONOS BLUETOOTH AL MEJOR PRECIO <3\n\n:) 1 unidad x 25 soles\n:D 3 unidades a mas x 17 soles (51 soles)\n\nSOMOS LK <3', tags: ['audifonos', 'bluetooth', 'tws', 'inalambrico', 'musica', 'gaming'] },
    { title: 'Set de Ollas Antiadherentes 8pz', price: '9', description: 'GENTE LLEGARON LAS OLLAS AL MEJOR PRECIO <3\n\n:) 1 unidad x 14 soles\n:D 3 unidades a mas x 9 soles (27 soles)\n\nSOMOS LK <3', tags: ['ollas', 'cocina', 'antiadherente', 'hogar', 'set', 'menaje'] },
    { title: 'Mochila Escolar Impermeable', price: '12', description: 'GENTE LLEGARON LAS MOCHILAS AL MEJOR PRECIO <3\n\n:) 1 unidad x 20 soles\n:D 3 unidades a mas x 12 soles (36 soles)\n\nSOMOS LK <3', tags: ['mochila', 'escolar', 'impermeable', 'viaje', 'resistente'] },
  ]
  const demoLoad = () => {
    setItems(demoSamples.map((s, i) => ({ page: i + 1, filename: `demo_${i + 1}.png`, url: svgPlaceholder('Producto ' + (i + 1)), info: { ...s }, selected: true })))
    log('Productos de ejemplo cargados (modo demo)')
  }

  // ---------- Login ----------
  const login = async () => { log('Iniciando sesion en Facebook...'); await api('/api/login', { method: 'POST' }); refreshStatus() }
  const confirm2fa = async () => { await api('/api/2fa-confirm', { method: 'POST' }); log('2FA confirmado'); refreshStatus() }

  // ---------- Config ----------
  const saveCfg = async (patch) => {
    const next = { ...cfg, ...patch }; setCfg(next)
    await api('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(next) })
  }

  // ---------- Publicar (WebSocket) ----------
  const publish = () => {
    const sel = items.filter(x => x.selected)
    if (!sel.length) { log('No hay productos seleccionados'); return }
    if (!session.logged_in) { log('Inicia sesion en Facebook primero'); return }
    setBusy(true); setProgress({ done: 0, total: sel.length, ok: 0, fail: 0 })
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/api/ws/publish`)
    wsRef.current = ws
    ws.onopen = () => ws.send(JSON.stringify({ items: sel.map(s => ({ filename: s.filename, ...(s.info || {}) })) }))
    ws.onmessage = (ev) => {
      const d = JSON.parse(ev.data)
      if (d.type === 'log' || d.type === 'error') log((d.type === 'error' ? '[!] ' : '') + d.message)
      else if (d.type === 'start') log(`Iniciando: ${d.total} productos (quedan hoy: ${d.remaining_today})`)
      else if (d.type === 'item_start') log(`\n[${d.page}] ${d.filename}`)
      else if (d.type === 'waiting') log(`Esperando ~${d.seconds}s (anti-baneo)...`)
      else if (d.type === 'item_done') log(`  ${d.status === 'success' ? '[OK]' : '[x]'} ${d.title || ''}`)
      else if (d.type === 'progress') setProgress({ done: d.done, total: d.total, ok: d.ok, fail: d.fail })
      else if (d.type === 'done') { log(`\nListo: ${d.ok} ok, ${d.fail} fallos`); setBusy(false); loadHistory() }
    }
    ws.onclose = () => setBusy(false)
    ws.onerror = () => { log('Error de conexion WS'); setBusy(false) }
  }

  // ---------- Publicar via AGENTE (.exe del cliente, a traves del relay) ----------
  // Persistimos la licencia y derivamos el account_id en el navegador.
  useEffect(() => {
    localStorage.setItem('eleka_license', licenseKey)
    let stop = false
    if (!licenseKey.trim()) { setAccountId(''); setAgentOnline(false); return }
    accountIdFor(licenseKey).then(id => { if (!stop) setAccountId(id) })
    return () => { stop = true }
  }, [licenseKey])

  // Sondeamos si el agente de esta cuenta esta conectado al cloud.
  useEffect(() => {
    if (!accountId) return
    const check = async () => {
      try { const r = await api(`/api/agent/online?account_id=${accountId}`); setAgentOnline(!!r.online) }
      catch { /* ignorar */ }
    }
    check(); const t = setInterval(check, 4000); return () => clearInterval(t)
  }, [accountId])

  const publishViaAgent = async () => {
    const sel = items.filter(x => x.selected)
    if (!sel.length) { log('No hay productos seleccionados'); return }
    if (!accountId) { log('Introduce tu clave de licencia'); return }
    setBusy(true); setProgress({ done: 0, total: sel.length, ok: 0, fail: 0 })
    let ok = 0, fail = 0
    try {
      const payload = {
        account_id: accountId,
        items: sel.map(s => ({
          page: s.page, title: s.info?.title || '', price: s.info?.price || '',
          description: s.info?.description || '', tags: s.info?.tags || [], image_files: [s.filename],
        })),
        settings: { category: cfg.default_category, condition: cfg.default_condition },
      }
      const res = await api('/api/jobs/publish', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      })
      if (res.detail) { log('[!] ' + res.detail); setBusy(false); return }
      log(`Job ${res.job_id} -> ${res.status}` + (res.status === 'queued' ? ' (agente offline; se enviara al conectar)' : ''))
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${location.host}/api/jobs/ws/${res.job_id}`)
      wsRef.current = ws
      ws.onmessage = (ev) => {
        const d = JSON.parse(ev.data)
        if (d.type === 'subscribed') log(`Suscrito al job (estado: ${d.status})`)
        else if (d.type === 'job_accepted') log('El agente acepto el job')
        else if (d.type === 'status') log(`Agente: ${d.state}`)
        else if (d.type === 'progress') log((d.level === 'error' ? '[!] ' : '  ') + (d.message || ''))
        else if (d.type === 'item_done') {
          d.status === 'success' ? ok++ : fail++
          log(`  ${d.status === 'success' ? '[OK]' : '[x]'} ${d.title || ''}` + (d.error ? ` (${d.error})` : ''))
          setProgress({ done: ok + fail, total: sel.length, ok, fail })
        }
        else if (d.type === 'job_done') { log(`\nListo: ${d.ok} ok, ${d.fail} fallos`); setBusy(false); try { ws.close() } catch {} loadHistory() }
        else if (d.type === 'error') { log('[!] ' + d.message); setBusy(false) }
      }
      ws.onerror = () => { log('Error de conexion WS del job'); setBusy(false) }
    } catch (e) { log('Error publicando: ' + e); setBusy(false) }
  }

  const loadHistory = async () => setHistory(await api('/api/history'))
  useEffect(() => { if (tab === 'historial') loadHistory() }, [tab])

  const selCount = items.filter(x => x.selected).length

  return (
    <div className="app">
      <header className="hdr">
        <div className="brand"><span className="logo"><IcGrid size={20} /></span> Marketplace <b>Automation</b></div>
        <div className="status">
          <Badge on={health.ai_ready} label="IA" />
          <Badge on={session.logged_in} label="Facebook" />
          {!session.logged_in && <button className="btn sm" onClick={login} disabled={session.logging_in}>{session.logging_in ? 'Conectando...' : 'Iniciar sesion FB'}</button>}
          {session.needs_2fa && <button className="btn sm warn" onClick={confirm2fa}>Ya aprobe el 2FA</button>}
        </div>
      </header>

      {health.demo && (
        <div className="demo-banner">
          {health.ai_real
            ? <>MODO DEMO — el <b>análisis con IA es REAL</b> (Gemini analiza tus imágenes y genera título, precio y descripción). Solo la <b>publicación a Facebook está simulada</b> por seguridad. Sube un PDF o tus fotos y pulsa <b>Analizar</b>.</>
            : <>MODO DEMO — interfaz navegable. Login, análisis y publicación son <b>simulados</b> (no toca Facebook). Pulsa <b>"Cargar ejemplo"</b> para probar el flujo completo.</>}
        </div>
      )}

      <nav className="tabs">
        {['productos', 'publicar', 'historial'].map(t =>
          <button key={t} className={tab === t ? 'tab active' : 'tab'} onClick={() => setTab(t)}>{t.toUpperCase()}</button>)}
      </nav>

      <main>
        {tab === 'productos' && (
          <section>
            <div className="toolbar">
              <label className="btn"><IcFile /> Cargar PDF<input type="file" accept="application/pdf" hidden onChange={uploadPdf} /></label>
              <label className="btn"><IcImage /> Cargar fotos<input type="file" accept="image/*" multiple hidden onChange={e => { addImages(e.target.files); e.target.value = '' }} /></label>
              {health.demo && <button className="btn ghost" onClick={demoLoad}><IcSparkle /> Cargar ejemplo</button>}
              <button className="btn ghost" disabled={!items.length || busy} onClick={analyzeAll}><IcCpu /> Analizar todo (IA)</button>
              <button className="btn ghost" disabled={!items.length} onClick={() => setItems(a => a.map(x => ({ ...x, selected: true })))}>Seleccionar todo</button>
              {items.length > 0 && <button className="btn ghost" onClick={() => setItems([])}>Limpiar</button>}
              <span className="muted">{items.length} elementos · {selCount} seleccionados</span>
            </div>

            <div
              className={'dropzone' + (drag ? ' over' : '')}
              onDragOver={e => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={onDrop}
            >
              <IcClipboard size={18} />
              <span>Arrastra imágenes aquí, o <b>pega con Ctrl+V</b>, o usa <b>Cargar fotos</b> / <b>Cargar PDF</b>.</span>
            </div>

            <div className="grid">
              {items.map((it, idx) => (
                <div key={it.filename} className={'card' + (it.selected ? ' sel' : '')}>
                  <div className="card-top">
                    <input type="checkbox" checked={it.selected} onChange={() => toggle(idx)} />
                    <span>#{it.page}</span>
                  </div>
                  <img src={it.url} alt={it.filename} />
                  {!it.info
                    ? <button className="btn xs" disabled={it.analyzing} onClick={() => analyze(idx)}>{it.analyzing ? 'Analizando...' : <><IcCpu size={14} /> Analizar</>}</button>
                    : <div className="info">
                        <input value={it.info.title} onChange={e => editInfo(idx, 'title', e.target.value)} placeholder="Titulo" />
                        <input value={it.info.price} onChange={e => editInfo(idx, 'price', e.target.value)} placeholder="Precio" />
                        <textarea value={it.info.description} onChange={e => editInfo(idx, 'description', e.target.value)} rows={4} />
                        <div className="tags">{(it.info.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
                        <button className="btn xs ghost" onClick={() => analyze(idx, true)}><IcRefresh size={14} /> Re-analizar</button>
                      </div>}
                </div>
              ))}
            </div>
          </section>
        )}

        {tab === 'publicar' && cfg && (
          <section className="pub">
            <div className="cfg">
              <div className="agent-box">
                <h3>Publicación real (tu agente .exe)</h3>
                <Field label="Clave de licencia">
                  <input value={licenseKey} onChange={e => setLicenseKey(e.target.value)} placeholder="ELEKA-MKT-XXXX-XXXX-XXXX" />
                </Field>
                <p className="muted">
                  Agente: <span className={agentOnline ? 'dot-on' : 'dot-off'}>{agentOnline ? 'CONECTADO' : 'desconectado'}</span>
                  {accountId && <> · cuenta <code>{accountId}</code></>}
                </p>
                <button className="btn big" disabled={busy || !selCount || !accountId} onClick={publishViaAgent}>
                  <IcSend /> Publicar {selCount} con mi agente
                </button>
                {!agentOnline && accountId && <p className="muted">Abre <b>ElekaMarketplaceAgent.exe</b> en tu PC con esta licencia. Si está offline, el job queda en cola y se enviará al conectar.</p>}
              </div>

              <h3>Configuracion</h3>
              <Field label="Categoria"><input value={cfg.default_category} onChange={e => saveCfg({ default_category: e.target.value })} /></Field>
              <Field label="Condicion"><input value={cfg.default_condition} onChange={e => saveCfg({ default_condition: e.target.value })} /></Field>
              <Field label="Limite diario"><input type="number" value={cfg.max_listings_per_day} onChange={e => saveCfg({ max_listings_per_day: +e.target.value })} /></Field>
              <Field label="Reintentos"><input type="number" value={cfg.max_retries} onChange={e => saveCfg({ max_retries: +e.target.value })} /></Field>
              <Field label="Pausa entre posts (s)">
                <div className="row">
                  <input type="number" value={cfg.listing_min_gap} onChange={e => saveCfg({ listing_min_gap: +e.target.value })} />
                  <span>a</span>
                  <input type="number" value={cfg.listing_max_gap} onChange={e => saveCfg({ listing_max_gap: +e.target.value })} />
                </div>
              </Field>
              <p className="muted">Quedan hoy: <b>{cfg.remaining_today}</b> publicaciones</p>
              <button className="btn big ghost" disabled={busy || !selCount} onClick={publish}><IcSend /> Publicar (modo servidor / demo)</button>
              {progress && <div className="bar"><div style={{ width: `${(progress.done / progress.total) * 100}%` }} /></div>}
              {progress && <p className="muted">{progress.ok} ok · {progress.fail} fallos · {progress.done}/{progress.total}</p>}
            </div>
            <div className="console" ref={logRef}>
              {logLines.map((l, i) => <div key={i}>{l}</div>)}
            </div>
          </section>
        )}

        {tab === 'historial' && (
          <section>
            <div className="stats">
              <Stat n={history.summary.success || 0} l="Publicados" />
              <Stat n={history.summary.failed || 0} l="Fallidos" />
              <Stat n={history.summary.today || 0} l="Hoy" />
              <Stat n={history.summary.total || 0} l="Total" />
            </div>
            <table className="tbl">
              <thead><tr><th>Fecha</th><th>Titulo</th><th>Precio</th><th>Estado</th><th>Intentos</th></tr></thead>
              <tbody>
                {history.records.map((r, i) => (
                  <tr key={i}>
                    <td>{r.timestamp?.replace('T', ' ')}</td>
                    <td>{r.title}</td>
                    <td>S/{r.price}</td>
                    <td><span className={'pill ' + r.status}>{r.status}</span></td>
                    <td>{r.attempts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </main>
    </div>
  )
}

const Badge = ({ on, label }) => <span className={'badge ' + (on ? 'ok' : 'off')}>{label}</span>
const Field = ({ label, children }) => <div className="fld"><label>{label}</label>{children}</div>
const Stat = ({ n, l }) => <div className="statcard"><b>{n}</b><span>{l}</span></div>
