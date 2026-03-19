import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { UserCog, Search, RefreshCcw, ListTree, BarChart3, History, Brain } from 'lucide-react';

const Admin = () => {
  const [users, setUsers] = useState([]);
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [targetUsername, setTargetUsername] = useState('');
  const [amount, setAmount] = useState('');
  const [mode, setMode] = useState('topup');
  const [result, setResult] = useState('');
  const [inspectUser, setInspectUser] = useState('');
  const [tab, setTab] = useState('portfolio'); // portfolio | trades | options | emotions
  const [inspectLoading, setInspectLoading] = useState(false);
  const [portfolio, setPortfolio] = useState([]);
  const [trades, setTrades] = useState([]);
  const [options, setOptions] = useState([]);
  const [emotions, setEmotions] = useState([]);

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await axios.get(`/admin/users${q ? `?q=${encodeURIComponent(q)}` : ''}`);
      setUsers(resp.data || []);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setResult('');
    setError('');
    try {
      const endpoint = mode === 'set' ? '/admin/balance/set' : '/admin/balance/topup';
      const resp = await axios.post(endpoint, {
        username: targetUsername,
        amount: Number(amount),
      });
      setResult(`${resp.data.username} balance: $${Number(resp.data.cash_balance).toLocaleString()}`);
      await fetchUsers();
    } catch (e2) {
      setError(e2?.response?.data?.detail || e2?.message || 'Failed to update balance');
    }
  };

  const loadInspect = async (u, t = tab) => {
    if (!u) return;
    setInspectLoading(true);
    setError('');
    try {
      if (t === 'portfolio') {
        const resp = await axios.get(`/admin/user/${encodeURIComponent(u)}/portfolio`);
        setPortfolio(resp.data || []);
      } else if (t === 'trades') {
        const resp = await axios.get(`/admin/user/${encodeURIComponent(u)}/trades`);
        setTrades(resp.data || []);
      } else if (t === 'options') {
        const resp = await axios.get(`/admin/user/${encodeURIComponent(u)}/options`);
        setOptions(resp.data || []);
      } else if (t === 'emotions') {
        const resp = await axios.get(`/admin/user/${encodeURIComponent(u)}/emotions`);
        setEmotions(resp.data || []);
      }
    } catch (e3) {
      setError(e3?.response?.data?.detail || e3?.message || 'Failed to load data');
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <UserCog className="text-blue-500" /> Admin Console
          </h1>
          <p className="text-slate-400">Manage user balances</p>
        </div>
        <button onClick={fetchUsers} className="btn-primary flex items-center gap-2">
          <RefreshCcw size={18} /> Refresh
        </button>
      </div>

      <div className="card p-6">
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-widest">Username</label>
            <input value={targetUsername} onChange={(e) => setTargetUsername(e.target.value)} className="input-field" placeholder="e.g. testuser" required />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-widest">Amount</label>
            <input value={amount} onChange={(e) => setAmount(e.target.value)} className="input-field" placeholder="e.g. 5000" required />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase mb-2 tracking-widest">Mode</label>
            <select value={mode} onChange={(e) => setMode(e.target.value)} className="input-field">
              <option value="topup">Top Up (+)</option>
              <option value="set">Set (=)</option>
            </select>
          </div>
          <button className="btn-secondary h-11" type="submit">Apply</button>
        </form>
        {result && <p className="mt-4 text-emerald-500 font-bold">{result}</p>}
        {error && <p className="mt-4 text-rose-500 font-bold">{error}</p>}
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-xl font-bold">Users</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchUsers()}
              className="bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 w-64"
              placeholder="Search username…"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-700/50 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="px-4 py-3">Username</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3 text-right">Cash Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-700/30 transition-colors cursor-pointer" onClick={() => { setInspectUser(u.username); setTab('portfolio'); loadInspect(u.username, 'portfolio'); }}>
                    <td className="px-4 py-3 font-bold text-white underline decoration-dotted">{u.username}</td>
                    <td className="px-4 py-3 text-slate-300">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase ${u.is_admin ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' : 'bg-slate-600/10 text-slate-300 border border-slate-600/30'}`}>
                        {u.is_admin ? 'ADMIN' : 'USER'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400">${Number(u.cash_balance || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {inspectUser && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold">Inspect: {inspectUser}</h2>
              <p className="text-slate-400 text-xs">Holdings, trades, emotions, and options</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                className={`px-3 py-2 rounded-md text-xs font-bold uppercase tracking-widest border ${tab === 'portfolio' ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-300 hover:bg-slate-800'}`}
                onClick={() => { setTab('portfolio'); loadInspect(inspectUser, 'portfolio'); }}
                title="Portfolio"
              >
                <ListTree size={14} className="inline mr-2" /> Portfolio
              </button>
              <button
                className={`px-3 py-2 rounded-md text-xs font-bold uppercase tracking-widest border ${tab === 'trades' ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-300 hover:bg-slate-800'}`}
                onClick={() => { setTab('trades'); loadInspect(inspectUser, 'trades'); }}
                title="Trades"
              >
                <History size={14} className="inline mr-2" /> Trades
              </button>
              <button
                className={`px-3 py-2 rounded-md text-xs font-bold uppercase tracking-widest border ${tab === 'options' ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-300 hover:bg-slate-800'}`}
                onClick={() => { setTab('options'); loadInspect(inspectUser, 'options'); }}
                title="Options"
              >
                <BarChart3 size={14} className="inline mr-2" /> Options
              </button>
              <button
                className={`px-3 py-2 rounded-md text-xs font-bold uppercase tracking-widest border ${tab === 'emotions' ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-300 hover:bg-slate-800'}`}
                onClick={() => { setTab('emotions'); loadInspect(inspectUser, 'emotions'); }}
                title="Emotions"
              >
                <Brain size={14} className="inline mr-2" /> Emotions
              </button>
            </div>
          </div>

          {inspectLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : tab === 'portfolio' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-700/50 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-4 py-3">Symbol</th>
                    <th className="px-4 py-3">Quantity</th>
                    <th className="px-4 py-3">Avg Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {portfolio.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3 font-bold text-white">{p.stock_symbol}</td>
                      <td className="px-4 py-3">{p.quantity}</td>
                      <td className="px-4 py-3">${Number(p.avg_price).toFixed(2)}</td>
                    </tr>
                  ))}
                  {portfolio.length === 0 && <tr><td className="px-4 py-6 text-slate-500" colSpan="3">No holdings</td></tr>}
                </tbody>
              </table>
            </div>
          ) : tab === 'trades' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-700/50 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-4 py-3">Time</th>
                    <th className="px-4 py-3">Symbol</th>
                    <th className="px-4 py-3">Side</th>
                    <th className="px-4 py-3">Qty</th>
                    <th className="px-4 py-3">Price</th>
                    <th className="px-4 py-3">Emotion</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {trades.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3 text-xs text-slate-400">{new Date(t.timestamp).toLocaleString()}</td>
                      <td className="px-4 py-3 font-bold text-white">{t.stock_symbol}</td>
                      <td className={`px-4 py-3 font-bold ${t.trade_type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>{t.trade_type}</td>
                      <td className="px-4 py-3">{t.quantity}</td>
                      <td className="px-4 py-3">${Number(t.price).toFixed(2)}</td>
                      <td className="px-4 py-3 text-xs text-slate-400">{t.emotional_state || '-'}</td>
                    </tr>
                  ))}
                  {trades.length === 0 && <tr><td className="px-4 py-6 text-slate-500" colSpan="6">No trades</td></tr>}
                </tbody>
              </table>
            </div>
          ) : tab === 'options' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-700/50 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-4 py-3">Contract</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Entry</th>
                    <th className="px-4 py-3">Exit</th>
                    <th className="px-4 py-3">Opened</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {options.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3 font-bold text-white">{o.underlying_symbol} {o.option_type} {o.strike} {o.expiry} x{o.contracts}</td>
                      <td className="px-4 py-3">{o.status}</td>
                      <td className="px-4 py-3">${Number(o.entry_price).toFixed(2)}</td>
                      <td className="px-4 py-3">{o.exit_price != null ? `$${Number(o.exit_price).toFixed(2)}` : '-'}</td>
                      <td className="px-4 py-3 text-xs text-slate-400">{new Date(o.opened_at).toLocaleString()}</td>
                    </tr>
                  ))}
                  {options.length === 0 && <tr><td className="px-4 py-6 text-slate-500" colSpan="5">No options</td></tr>}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-slate-700/50 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="px-4 py-3">Time</th>
                    <th className="px-4 py-3">Emotion</th>
                    <th className="px-4 py-3">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {emotions.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3 text-xs text-slate-400">{new Date(e.timestamp).toLocaleString()}</td>
                      <td className="px-4 py-3 font-bold text-white capitalize">{e.emotion}</td>
                      <td className="px-4 py-3">{(Number(e.confidence) * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                  {emotions.length === 0 && <tr><td className="px-4 py-6 text-slate-500" colSpan="3">No logs</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Admin;
