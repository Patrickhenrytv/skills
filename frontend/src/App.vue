<template>
  <div id="app-root">

    <!-- ═══ NAV ═══ -->
    <nav>
      <div class="logo">
        <div class="logo-icon">📊</div>
        <span>SentimentTracker</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <span id="networkBadge" class="nav-badge" :class="connected ? 'badge-connected' : ''">
          {{ connected ? '🟢 Studionet' : '⚫ Disconnected' }}
        </span>
        <a href="https://docs.genlayer.com" target="_blank" class="btn btn-secondary docs-btn">Docs ↗</a>
      </div>
    </nav>

    <!-- ═══ HERO ═══ -->
    <div class="hero">
      <div class="hero-glow"></div>
      <h1>AI Sentiment Intelligence</h1>
      <p>Submit any topic and URL — the GenLayer AI analyzes real-time sentiment and stores results permanently on-chain.</p>

      <div class="contract-bar">
        <input
          id="contractInput"
          v-model="contractInput"
          type="text"
          placeholder="Paste your contract address: 0x..."
          @keyup.enter="connectContract"
        />
        <button class="btn btn-primary" @click="connectContract">Connect</button>
      </div>
      <div v-if="connectError" class="connect-error">⚠️ {{ connectError }}</div>
    </div>

    <!-- ═══ STATS ═══ -->
    <div class="stats">
      <div class="stat-card">
        <div class="stat-num" id="statTotal">{{ stats.total ?? '—' }}</div>
        <div class="stat-label">Total Analyses</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" id="statTopics">{{ stats.topics ?? '—' }}</div>
        <div class="stat-label">Topics Tracked</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" id="statLatestScore">{{ stats.latestScore ?? '—' }}</div>
        <div class="stat-label">Latest Score</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" :style="sentimentColor(stats.latestSentiment)" id="statLatestSentiment">
          {{ stats.latestSentiment ?? '—' }}
        </div>
        <div class="stat-label">Latest Sentiment</div>
      </div>
    </div>

    <!-- ═══ MAIN GRID ═══ -->
    <div class="main">

      <!-- LEFT PANEL -->
      <div class="left-col">

        <!-- Analyze Panel -->
        <div class="panel">
          <div class="panel-title"><span>🔍</span> Analyze Topic</div>

          <div class="form-group">
            <label>Topic</label>
            <input id="topicInput" v-model="form.topic" type="text" placeholder="e.g. Bitcoin, GenLayer, AI regulation" />
            <div class="quick-topics">
              <span class="chip" v-for="t in quickTopics" :key="t" @click="form.topic = t">{{ t }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>Source URL</label>
            <input id="urlInput" v-model="form.url" type="url" placeholder="https://en.wikipedia.org/wiki/..." />
            <div class="quick-topics">
              <span class="chip" v-for="u in quickUrls" :key="u.label" @click="form.url = u.url">{{ u.label }}</span>
            </div>
          </div>

          <button class="analyze-btn" id="analyzeBtn" @click="analyze" :disabled="!connected || analyzing">
            <div v-if="analyzing" class="spinner"></div>
            <span>{{ analyzing ? 'Analyzing...' : connected ? '🚀 Analyze Sentiment' : '🔗 Connect contract first' }}</span>
          </button>

          <div v-if="analyzeStatus.msg" class="status" :class="analyzeStatus.type" id="analyzeStatus">
            <div v-if="analyzeStatus.type === 'loading'" class="spinner"></div>
            <span>{{ analyzeStatus.type === 'success' ? '✅' : analyzeStatus.type === 'error' ? '❌' : '' }}</span>
            <span>{{ analyzeStatus.msg }}</span>
          </div>
        </div>

        <!-- Query Panel -->
        <div class="panel">
          <div class="panel-title"><span>📜</span> Query History</div>
          <div class="form-group">
            <label>Topic to query</label>
            <input id="queryInput" v-model="queryTopic" type="text" placeholder="e.g. Bitcoin" @keyup.enter="queryLatest" />
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn btn-secondary" style="flex:1" id="latestBtn" @click="queryLatest" :disabled="!connected">Latest</button>
            <button class="btn btn-secondary" style="flex:1" id="historyBtn" @click="queryHistory" :disabled="!connected">Full History</button>
            <button class="btn btn-secondary" style="flex:1" id="avgBtn" @click="queryAvg" :disabled="!connected">Avg Score</button>
          </div>
          <div v-if="queryStatus.msg" class="status" :class="queryStatus.type" id="queryStatus">
            <div v-if="queryStatus.type === 'loading'" class="spinner"></div>
            <span>{{ queryStatus.type === 'success' ? '✅' : queryStatus.type === 'error' ? '❌' : '' }}</span>
            <span>{{ queryStatus.msg }}</span>
          </div>
        </div>

        <!-- RPC Info Panel -->
        <div class="panel rpc-panel">
          <div class="panel-title"><span>⚙️</span> Network Config</div>
          <div class="rpc-row"><span class="rpc-key">RPC URL</span><code>https://studio.genlayer.com/api</code></div>
          <div class="rpc-row"><span class="rpc-key">Chain ID</span><code>61999</code></div>
          <div class="rpc-row"><span class="rpc-key">Symbol</span><code>GEN</code></div>
          <div class="rpc-hint">Add these to Rabby / MetaMask to send write transactions.</div>
        </div>

      </div>

      <!-- RIGHT: Results -->
      <div class="results-area" id="resultsArea">
        <div v-if="results.length === 0" class="empty">
          <span class="empty-icon">🧠</span>
          <h3>No results yet</h3>
          <p>Connect your contract and run an analysis to see AI sentiment results here.</p>
        </div>
        <TransitionGroup name="card" tag="div">
          <div
            v-for="(entry, i) in results"
            :key="entry._id || i"
            class="result-card"
          >
            <div class="result-header">
              <div>
                <div class="result-topic">{{ entry.topic }}</div>
                <div class="result-time">{{ timeAgo(entry.timestamp) }}</div>
              </div>
              <span class="sentiment-badge" :class="badgeClass(entry.sentiment)">{{ entry.sentiment }}</span>
            </div>
            <div class="score-section">
              <div class="score-label">
                <span>Sentiment Score</span>
                <span :style="{ color: scoreColor(+entry.score), fontWeight: 700 }">{{ entry.score }}/100</span>
              </div>
              <div class="score-bar-bg">
                <div class="score-bar-fill" :style="{ width: entry.score + '%', background: scoreColor(+entry.score) }"></div>
              </div>
            </div>
            <div class="result-summary">💬 {{ entry.summary || 'No summary available.' }}</div>
            <div class="result-url">
              🔗 <a :href="entry.source_url" target="_blank">{{ entry.source_url }}</a>
            </div>
            <div v-if="entry.submitted_by" class="result-url">👤 {{ entry.submitted_by }}</div>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <!-- ═══ FOOTER ═══ -->
    <footer>
      Built on <a href="https://genlayer.com" target="_blank">GenLayer</a> — AI-powered Intelligent Contracts &nbsp;|&nbsp;
      <a href="https://docs.genlayer.com" target="_blank">Documentation</a> &nbsp;|&nbsp;
      <a href="https://studio.genlayer.com" target="_blank">Studio</a>
    </footer>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

// ─── Config ──────────────────────────────────────────────────────────────────
const RPC_URL       = import.meta.env.VITE_RPC_URL || 'https://studio.genlayer.com/api'
const ENV_CONTRACT  = import.meta.env.VITE_CONTRACT_ADDRESS || ''

// ─── State ───────────────────────────────────────────────────────────────────
const contractAddress = ref(ENV_CONTRACT)
const contractInput   = ref(ENV_CONTRACT)
const connected       = ref(false)
const analyzing       = ref(false)
const connectError    = ref('')
const queryTopic      = ref('')
const results         = ref<any[]>([])
let   resultCounter   = 0

const form = reactive({ topic: '', url: '' })
const analyzeStatus = reactive({ type: '', msg: '' })
const queryStatus   = reactive({ type: '', msg: '' })
const stats = reactive({ total: null as any, topics: null as any, latestScore: null as any, latestSentiment: null as any })

// ─── Quick Suggestions ───────────────────────────────────────────────────────
const quickTopics = ['Bitcoin', 'Ethereum', 'GenLayer', 'AI', 'Elon Musk']
const quickUrls = [
  { label: 'Bitcoin Wiki',  url: 'https://en.wikipedia.org/wiki/Bitcoin' },
  { label: 'Ethereum Wiki', url: 'https://en.wikipedia.org/wiki/Ethereum' },
  { label: 'GenLayer',      url: 'https://genlayer.com' },
  { label: 'OpenAI',        url: 'https://openai.com' },
]

// ─── RPC ─────────────────────────────────────────────────────────────────────
async function rpcCall(method: string, params: any) {
  const res = await fetch(RPC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params })
  })
  const json = await res.json()
  if (json.error) throw new Error(json.error.message || JSON.stringify(json.error))
  return json.result
}

async function callContract(fn: string, args: any[] = []) {
  return rpcCall('gen_call', { to: contractAddress.value, data: { method: fn, args } })
}

// ─── Connect ─────────────────────────────────────────────────────────────────
async function connectContract() {
  const addr = contractInput.value.trim()
  if (!addr) { connectError.value = 'Please paste a contract address.'; return }
  if (!addr.startsWith('0x')) { connectError.value = 'Address must start with 0x'; return }
  contractAddress.value = addr
  connectError.value = ''
  connected.value = true
  await loadStats()
}

// ─── Stats ────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const total = await callContract('get_total_analyses')
    stats.total = Number(total) || 0
  } catch { stats.total = '?' }
}

// ─── Analyze (Write) ─────────────────────────────────────────────────────────
async function analyze() {
  if (!form.topic) { alert('Enter a topic'); return }
  if (!form.url)   { alert('Enter a source URL'); return }

  analyzing.value = true
  setStatus(analyzeStatus, 'loading', 'Sending transaction to GenLayer validators...')

  try {
    await rpcCall('gen_sendTransaction', {
      to:   contractAddress.value,
      data: { method: 'analyze', args: [form.topic, form.url] }
    })

    setStatus(analyzeStatus, 'success', `Transaction submitted! Validators are analyzing "${form.topic}" — results appear shortly.`)
    stats.topics = (stats.topics || 0) + 1

    // Poll for result after validators settle
    setTimeout(async () => {
      try {
        const entry = await callContract('get_latest', [form.topic])
        if (entry) pushResult(entry)
        await loadStats()
      } catch {}
    }, 5000)

  } catch (e: any) {
    setStatus(analyzeStatus, 'error', `Write tx requires a wallet. CLI: genlayer write --contract ${contractAddress.value} analyze "${form.topic}" "${form.url}"`)
    // Show a preview card so the user sees what data will look like
    pushResult({
      topic: form.topic, sentiment: 'neutral', score: 50,
      summary: 'Preview card — real data will appear after the validator network processes your transaction.',
      source_url: form.url, submitted_by: '', timestamp: Math.floor(Date.now() / 1000)
    })
  } finally {
    analyzing.value = false
  }
}

// ─── Query (Read) ─────────────────────────────────────────────────────────────
async function queryLatest() {
  const t = queryTopic.value.trim()
  if (!t) { alert('Enter a topic to query'); return }
  setStatus(queryStatus, 'loading', `Fetching latest for "${t}"...`)
  try {
    const entry = await callContract('get_latest', [t])
    clearStatus(queryStatus)
    if (!entry) { setStatus(queryStatus, 'error', `No analysis found for "${t}"`); return }
    pushResult(entry)
  } catch (e: any) { setStatus(queryStatus, 'error', `Error: ${e.message}`) }
}

async function queryHistory() {
  const t = queryTopic.value.trim()
  if (!t) { alert('Enter a topic to query'); return }
  setStatus(queryStatus, 'loading', `Fetching history for "${t}"...`)
  try {
    const entries = await callContract('get_history', [t])
    clearStatus(queryStatus)
    if (!entries || entries.length === 0) { setStatus(queryStatus, 'error', `No history for "${t}"`); return }
    results.value = []
    entries.forEach((e: any) => pushResult(e))
  } catch (e: any) { setStatus(queryStatus, 'error', `Error: ${e.message}`) }
}

async function queryAvg() {
  const t = queryTopic.value.trim()
  if (!t) { alert('Enter a topic to query'); return }
  setStatus(queryStatus, 'loading', `Computing average score for "${t}"...`)
  try {
    const avg = await callContract('get_average_score', [t])
    setStatus(queryStatus, 'success', `Average sentiment score for "${t}": ${avg}/100`)
    stats.latestScore = avg
  } catch (e: any) { setStatus(queryStatus, 'error', `Error: ${e.message}`) }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function pushResult(entry: any) {
  const enriched = { ...entry, _id: ++resultCounter }
  results.value.unshift(enriched)
  stats.latestScore     = entry.score
  stats.latestSentiment = entry.sentiment
}

function setStatus(obj: any, type: string, msg: string) {
  obj.type = type; obj.msg = msg
}
function clearStatus(obj: any) { obj.type = ''; obj.msg = '' }

function scoreColor(score: number) {
  if (score >= 70) return '#22c55e'
  if (score >= 45) return '#f59e0b'
  return '#ef4444'
}

function sentimentColor(s: string | null) {
  if (!s) return {}
  const map: Record<string, string> = { positive: '#22c55e', negative: '#ef4444', neutral: '#94a3b8', mixed: '#f59e0b' }
  return { color: map[s] || '#94a3b8' }
}

function badgeClass(s: string) {
  const map: Record<string, string> = { positive: 'badge-positive', negative: 'badge-negative', neutral: 'badge-neutral', mixed: 'badge-mixed' }
  return map[s] || 'badge-neutral'
}

function timeAgo(ts: any) {
  if (!ts) return ''
  return new Date(Number(ts) * 1000).toLocaleString()
}

// Auto-connect if env has address
onMounted(() => {
  if (ENV_CONTRACT && ENV_CONTRACT !== '0xYOUR_CONTRACT_ADDRESS_HERE') {
    connectContract()
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* NAV */
nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 40px; border-bottom: 1px solid var(--border);
  background: rgba(10,10,15,0.95); backdrop-filter: blur(12px);
  position: sticky; top: 0; z-index: 100;
}
.logo { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 700; }
.logo-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
}
.nav-badge {
  padding: 4px 12px; border-radius: 20px; font-size: .75rem; font-weight: 600;
  background: rgba(124,92,252,0.15); border: 1px solid rgba(124,92,252,0.3); color: var(--accent);
  transition: all .3s;
}
.badge-connected {
  background: rgba(34,197,94,0.15) !important; border-color: rgba(34,197,94,0.3) !important; color: var(--green) !important;
}
.docs-btn { padding: 8px 16px; font-size: .82rem; text-decoration: none; }

/* HERO */
.hero {
  padding: 60px 40px 40px; text-align: center; position: relative; overflow: hidden;
}
.hero-glow {
  position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
  width: 600px; height: 300px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(124,92,252,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.hero h1 {
  font-size: 2.8rem; font-weight: 700;
  background: linear-gradient(135deg, #fff 30%, var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}
.hero p { color: var(--muted); font-size: 1.05rem; max-width: 520px; margin: 0 auto 32px; }

.contract-bar {
  display: flex; gap: 12px; max-width: 680px; margin: 0 auto; align-items: center;
}
.contract-bar input {
  flex: 1; padding: 14px 18px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--card); color: var(--text);
  font-family: monospace; font-size: .9rem; outline: none; transition: .2s;
}
.contract-bar input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,92,252,.15); }
.contract-bar input::placeholder { color: var(--gray); }
.connect-error { color: var(--red); font-size: .82rem; margin-top: 8px; }

/* BUTTONS */
.btn {
  padding: 13px 22px; border-radius: var(--radius); border: none; cursor: pointer;
  font-family: 'Inter', sans-serif; font-size: .9rem; font-weight: 600; transition: .2s;
  white-space: nowrap;
}
.btn-primary { background: linear-gradient(135deg, var(--accent), var(--accent2)); color: #fff; }
.btn-primary:hover { opacity: .88; transform: translateY(-1px); }
.btn-secondary { background: var(--card); border: 1px solid var(--border); color: var(--text); }
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
.btn-secondary:disabled { opacity: .4; cursor: not-allowed; }

/* STATS */
.stats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px; max-width: 900px; margin: 40px auto 0; padding: 0 40px;
}
.stat-card {
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 22px; text-align: center; transition: .2s;
}
.stat-card:hover { border-color: var(--accent); box-shadow: var(--glow); }
.stat-num { font-size: 2rem; font-weight: 700; color: var(--accent); text-transform: capitalize; }
.stat-label { font-size: .8rem; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: .05em; }

/* MAIN */
.main {
  display: grid; grid-template-columns: 380px 1fr;
  gap: 24px; padding: 32px 40px; max-width: 1400px; margin: 0 auto;
}
@media (max-width: 900px) { .main { grid-template-columns: 1fr; } }
.left-col { display: flex; flex-direction: column; gap: 20px; }

/* PANELS */
.panel {
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px;
}
.panel-title { font-size: 1rem; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: .82rem; color: var(--muted); margin-bottom: 6px; font-weight: 500; }
.form-group input {
  width: 100%; padding: 12px 14px; border-radius: 10px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text); font-family: 'Inter', sans-serif; font-size: .9rem; outline: none; transition: .2s;
}
.form-group input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,92,252,.1); }
.form-group input::placeholder { color: var(--gray); }

.quick-topics { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.chip {
  padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border);
  background: var(--surface); font-size: .78rem; cursor: pointer; color: var(--muted); transition: .2s;
}
.chip:hover { border-color: var(--accent); color: var(--accent); }

.analyze-btn {
  width: 100%; padding: 14px; margin-top: 8px; border-radius: 12px; border: none;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #fff; font-family: 'Inter', sans-serif; font-size: .95rem; font-weight: 600;
  cursor: pointer; transition: .2s; display: flex; align-items: center; justify-content: center; gap: 8px;
}
.analyze-btn:hover:not(:disabled) { opacity: .88; transform: translateY(-1px); }
.analyze-btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }

/* STATUS */
.status {
  margin-top: 14px; padding: 12px 16px; border-radius: 10px;
  font-size: .85rem; display: flex; align-items: center; gap: 8px;
}
.loading { background: rgba(124,92,252,.1); border: 1px solid rgba(124,92,252,.2); color: var(--accent); }
.success { background: rgba(34,197,94,.1); border: 1px solid rgba(34,197,94,.2); color: var(--green); }
.error   { background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.2); color: var(--red); font-size: .8rem; word-break: break-all; }

.spinner {
  width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent;
  border-radius: 50%; animation: spin .7s linear infinite; flex-shrink: 0;
}

/* RPC PANEL */
.rpc-panel { font-size: .82rem; }
.rpc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.rpc-key { color: var(--muted); min-width: 70px; font-weight: 500; }
.rpc-row code {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 4px 8px; font-size: .78rem; color: var(--accent);
  word-break: break-all;
}
.rpc-hint { color: var(--gray); font-size: .78rem; margin-top: 8px; }

/* RESULTS */
.results-area { display: flex; flex-direction: column; gap: 20px; }
.empty { text-align: center; padding: 60px 20px; color: var(--gray); }
.empty-icon { font-size: 3.5rem; margin-bottom: 16px; display: block; }
.empty h3 { font-size: 1rem; font-weight: 600; color: var(--muted); margin-bottom: 6px; }
.empty p { font-size: .85rem; }

.result-card {
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 22px; transition: .2s;
}
.result-card:hover { border-color: rgba(124,92,252,.4); box-shadow: var(--glow); }
.result-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; }
.result-topic { font-size: 1.1rem; font-weight: 700; }
.result-time { font-size: .75rem; color: var(--gray); margin-top: 3px; }
.sentiment-badge {
  padding: 6px 14px; border-radius: 20px; font-size: .82rem; font-weight: 700; text-transform: capitalize; white-space: nowrap;
}
.badge-positive { background: rgba(34,197,94,.15); color: var(--green); border: 1px solid rgba(34,197,94,.3); }
.badge-negative { background: rgba(239,68,68,.15); color: var(--red); border: 1px solid rgba(239,68,68,.3); }
.badge-neutral  { background: rgba(148,163,184,.15); color: var(--muted); border: 1px solid rgba(148,163,184,.3); }
.badge-mixed    { background: rgba(245,158,11,.15); color: var(--yellow); border: 1px solid rgba(245,158,11,.3); }

.score-section { margin: 14px 0; }
.score-label { font-size: .78rem; color: var(--muted); margin-bottom: 6px; display: flex; justify-content: space-between; }
.score-bar-bg { height: 8px; background: var(--surface); border-radius: 4px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 4px; transition: width 1s cubic-bezier(.4,0,.2,1); }

.result-summary {
  font-size: .88rem; color: var(--muted); line-height: 1.6; margin-top: 10px;
  padding: 12px; background: var(--surface); border-radius: 8px;
}
.result-url {
  font-size: .75rem; color: var(--gray); margin-top: 10px;
  display: flex; align-items: center; gap: 6px; word-break: break-all;
}
.result-url a { color: var(--accent); text-decoration: none; }
.result-url a:hover { text-decoration: underline; }

/* Vue Transition for cards */
.card-enter-active { animation: fadeIn .4s ease; }
.card-leave-active { transition: opacity .2s; }
.card-leave-to { opacity: 0; }

/* FOOTER */
footer {
  text-align: center; padding: 32px; color: var(--gray);
  font-size: .8rem; border-top: 1px solid var(--border); margin-top: 20px;
}
footer a { color: var(--accent); text-decoration: none; }
footer a:hover { text-decoration: underline; }
</style>
