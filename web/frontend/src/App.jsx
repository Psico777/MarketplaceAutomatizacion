import React, { useState, useEffect, useRef } from 'react'

const api = (p, opts) => fetch(p, opts).then(r => r.json())

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
      if (d.type === 'log' || d.type === 'error') log((d.type === 'error' ? '⛔ ' : '') + d.message)
      else if (d.type === 'start') log(`Iniciando: ${d.total} productos (quedan hoy: ${d.remaining_today})`)
      else if (d.type === 'item_start') log(`\n[${d.page}] ${d.filename}`)
      else if (d.type === 'waiting') log(`Esperando ~${d.seconds}s (anti-baneo)...`)
      else if (d.type === 'item_done') log(`  ${d.status === 'success' ? '✓' : '✗'} ${d.title || ''}`)
      else if (d.type === 'progress') setProgress({ done: d.done, total: d.total, ok: d.ok, fail: d.fail })
      else if (d.type === 'done') { log(`\nListo: ${d.ok} ok, ${d.fail} fallos`); setBusy(false); loadHistory() }
    }
    ws.onclose = () => setBusy(false)
    ws.onerror = () => { log('Error de conexion WS'); setBusy(false) }
  }

  const loadHistory = async () => setHistory(await api('/api/history'))
  useEffect(() => { if (tab === 'historial') loadHistory() }, [tab])

  const selCount = items.filter(x => x.selected).length

  return (
    <div className="app">
      <header className="hdr">
        <div className="brand"><span className="logo">◧</span> Marketplace <b>Automation</b></div>
        <div className="status">
          <Badge on={health.ai_ready} label="IA" />
          <Badge on={session.logged_in} label="Facebook" />
          {!session.logged_in && <button className="btn sm" onClick={login} disabled={session.logging_in}>{session.logging_in ? 'Conectando...' : 'Iniciar sesion FB'}</button>}
          {session.needs_2fa && <button className="btn sm warn" onClick={confirm2fa}>Ya aprobe el 2FA</button>}
        </div>
      </header>

      <nav className="tabs">
        {['productos', 'publicar', 'historial'].map(t =>
          <button key={t} className={tab === t ? 'tab active' : 'tab'} onClick={() => setTab(t)}>{t.toUpperCase()}</button>)}
      </nav>

      <main>
        {tab === 'productos' && (
          <section>
            <div className="toolbar">
              <label className="btn">📄 Cargar PDF<input type="file" accept="application/pdf" hidden onChange={uploadPdf} /></label>
              <button className="btn ghost" disabled={!items.length || busy} onClick={analyzeAll}>🤖 Analizar todo (IA)</button>
              <button className="btn ghost" disabled={!items.length} onClick={() => setItems(a => a.map(x => ({ ...x, selected: true })))}>Seleccionar todo</button>
              <span className="muted">{items.length} paginas · {selCount} seleccionadas</span>
            </div>
            <div className="grid">
              {items.map((it, idx) => (
                <div key={it.filename} className={'card' + (it.selected ? ' sel' : '')}>
                  <div className="card-top">
                    <input type="checkbox" checked={it.selected} onChange={() => toggle(idx)} />
                    <span>Pag. {it.page}</span>
                  </div>
                  <img src={it.url} alt={it.filename} />
                  {!it.info
                    ? <button className="btn xs" disabled={it.analyzing} onClick={() => analyze(idx)}>{it.analyzing ? 'Analizando...' : '🤖 Analizar'}</button>
                    : <div className="info">
                        <input value={it.info.title} onChange={e => editInfo(idx, 'title', e.target.value)} placeholder="Titulo" />
                        <input value={it.info.price} onChange={e => editInfo(idx, 'price', e.target.value)} placeholder="Precio" />
                        <textarea value={it.info.description} onChange={e => editInfo(idx, 'description', e.target.value)} rows={4} />
                        <div className="tags">{(it.info.tags || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
                        <button className="btn xs ghost" onClick={() => analyze(idx, true)}>↻ Re-analizar</button>
                      </div>}
                </div>
              ))}
            </div>
          </section>
        )}

        {tab === 'publicar' && cfg && (
          <section className="pub">
            <div className="cfg">
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
              <button className="btn big" disabled={busy || !selCount} onClick={publish}>🚀 Publicar {selCount} seleccionados</button>
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
