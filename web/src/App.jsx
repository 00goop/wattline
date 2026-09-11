import { lazy, Suspense, useEffect, useState } from 'react'
import {
  fetchNpus,
  fetchStats,
  fetchSites,
  fetchExposureSeries,
  isUsingMock,
} from './api.js'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
const MapView = lazy(() => import('./components/MapView.jsx'))
import Scrubber from './components/Scrubber.jsx'
import NpuDetailPanel from './components/NpuDetailPanel.jsx'
import Landing from './components/Landing.jsx'
import './landing.css'

const HOURS = 25 // hour 0–24 inclusive (frozen contract)
const PLAY_STEP_MS = 600

export default function App() {
  // landing page is the entry screen; "Enter the map" switches to the dashboard
  const [view, setView] = useState('landing')
  const [npus, setNpus] = useState(null)
  const [stats, setStats] = useState(null)
  const [sites, setSites] = useState(null)
  const [mock, setMock] = useState(false)
  // All 25 hours prefetched on mount — the scrub must never be network-bound.
  const [series, setSeries] = useState(null)
  const [hour, setHour] = useState(0)
  const [playing, setPlaying] = useState(false)
  // F4: selected NPU (map click or sidebar row) → detail panel
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    let alive = true
    Promise.all([
      fetchNpus(),
      fetchStats(),
      fetchSites(),
      fetchExposureSeries(HOURS),
    ]).then(([n, s, st, hours]) => {
      if (!alive) return
      setNpus(n)
      setStats(s)
      setSites(st)
      setSeries(hours)
      setMock(isUsingMock())
    })
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    if (!playing || !series) return
    const t = setInterval(
      () => setHour((h) => Math.min(h + 1, HOURS - 1)),
      PLAY_STEP_MS,
    )
    return () => clearInterval(t)
  }, [playing, series])

  useEffect(() => {
    if (hour >= HOURS - 1) setPlaying(false)
  }, [hour])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && setSelectedId(null)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const exposure = series?.[hour] ?? null
  const selectedNpu = selectedId
    ? npus?.features.find((f) => f.properties.npu_id === selectedId)?.properties
    : null
  const selectedExp =
    selectedNpu && exposure
      ? exposure.npus.find((e) => e.npu_id === selectedId)
      : null

  const togglePlay = () => {
    if (!series) return
    if (!playing && hour >= HOURS - 1) setHour(0) // replay from the top
    setPlaying((p) => !p)
  }

  if (view === 'landing') {
    return <Landing onEnter={() => setView('map')} />
  }

  return (
    <div className="app">
      <Header stats={stats} mock={mock} exposure={exposure} onHome={() => setView('landing')} />
      <div className="main">
        <Sidebar
          npus={npus}
          exposure={exposure}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <Suspense fallback={<div className="map-wrap map-loading" role="status">Preparing the exposure map…</div>}>
        <MapView
          npus={npus}
          exposure={exposure}
          sites={sites}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        </Suspense>
        {selectedNpu && (
          <NpuDetailPanel
            npu={selectedNpu}
            exp={selectedExp}
            hour={hour}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>
      <Scrubber
        hour={hour}
        maxHour={HOURS - 1}
        setHour={setHour}
        playing={playing}
        onPlay={togglePlay}
        ready={!!series}
      />
    </div>
  )
}
