// Thin API client for the FastAPI backend. Dev server proxies /api -> :8000.
export async function getStats() {
  const r = await fetch('/api/stats'); return r.json()
}
export async function getTrades(limit = 200) {
  const r = await fetch(`/api/trades?limit=${limit}`); return r.json()
}
export async function runSim() {
  const r = await fetch('/api/run-sim', { method: 'POST' }); return r.json()
}
export async function getStrategies() {
  const r = await fetch('/api/strategies'); return r.json()
}
export async function validateStrategy(name) {
  const r = await fetch(`/api/strategies/${name}/validate`, { method: 'POST' }); return r.json()
}

export async function orchestrateTrade(ticker) {
  const r = await fetch('/api/agent/orchestrate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker })
  });
  return r.json();
}

export async function getAgentPositions() {
  const r = await fetch('/api/agent/positions');
  return r.json();
}

export async function closeAgentPosition(id) {
  const r = await fetch(`/api/agent/positions/${id}/close`, { method: 'POST' });
  return r.json();
}

