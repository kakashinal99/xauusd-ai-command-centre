const prices = [2318, 2320, 2317, 2324, 2322, 2327, 2325, 2331, 2328, 2334, 2332, 2337, 2335, 2340, 2338, 2344, 2341, 2346, 2343, 2349, 2347, 2352, 2348, 2354, 2351, 2357, 2354, 2359, 2356, 2362, 2359, 2365, 2361, 2367, 2364, 2370];
const min = Math.min(...prices);
const max = Math.max(...prices);
const points = prices.map((price, index) => {
  const x = (index / (prices.length - 1)) * 1000;
  const y = 190 - ((price - min) / (max - min)) * 150;
  return `${x},${y}`;
}).join(" ");

const strategies = [
  { name: "Donchian ATR", type: "Breakout", status: "Research", trades: "—", pf: "—" },
  { name: "Dow + Candlestick", type: "Structure", status: "Research", trades: "—", pf: "—" },
  { name: "RSI Mean Reversion", type: "Mean reversion", status: "Research", trades: "—", pf: "—" },
  { name: "Breakout + Retest", type: "Retest confirmation", status: "Research", trades: "—", pf: "—" }
];

function Icon({ children }: { children: React.ReactNode }) {
  return <span className="nav-icon" aria-hidden="true">{children}</span>;
}

export default function DashboardPage() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">X</div><div><strong>COMMAND CENTRE</strong><small>GOLD / XAUUSD</small></div></div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          <a className="active" href="#"><Icon>◫</Icon>Overview</a>
          <a href="#market"><Icon>⌁</Icon>Market monitor</a>
          <a href="#strategies"><Icon>◎</Icon>Strategies</a>
          <a href="#regime"><Icon>◈</Icon>Market regimes</a>
          <a href="#research"><Icon>▤</Icon>Research lab</a>
        </nav>
        <div className="sidebar-bottom"><span className="pulse" /> SYSTEM ONLINE <small>Research mode · Trading disabled</small></div>
      </aside>

      <section className="main">
        <header className="topbar">
          <div><div className="eyebrow">TRADING INTELLIGENCE / OVERVIEW</div><h1>Market overview</h1></div>
          <div className="top-actions"><span className="demo-pill">● DEMO DATA</span><div className="avatar">AI</div></div>
        </header>

        <div className="notice"><span>i</span><div><strong>Preview environment</strong><p>Illustrative market values only. Live Pepperstone cTrader data is not connected yet. No orders can be placed from this dashboard.</p></div></div>

        <section className="metric-grid" id="market">
          <article className="metric-card hero-metric"><div className="metric-head">XAUUSD <span>SPOT PRICE · SAMPLE</span></div><div className="price">$2,367.40 <b>+0.42%</b></div><div className="metric-foot">Bid $2,367.20 <i/> Ask $2,367.60</div></article>
          <article className="metric-card"><div className="metric-head">SPREAD <span>ILLUSTRATIVE</span></div><div className="metric-value">0.40 <small>USD</small></div><div className="metric-foot muted">Broker feed not connected</div></article>
          <article className="metric-card"><div className="metric-head">MARKET REGIME <span>HEURISTIC</span></div><div className="metric-value"><span className="regime-dot"/> Trending</div><div className="metric-foot muted">Sample classification only</div></article>
          <article className="metric-card"><div className="metric-head">TRADING MODE <span>SAFETY</span></div><div className="metric-value"><span className="lock">Ⅱ</span> Disabled</div><div className="metric-foot muted">Execution locked</div></article>
        </section>

        <section className="panel chart-panel">
          <div className="panel-heading"><div><div className="eyebrow">PRICE ACTION</div><h2>XAUUSD · M15</h2></div><div className="time-tabs"><button className="selected">15m</button><button>1H</button><button>4H</button><button>1D</button></div></div>
          <div className="chart-summary"><strong>$2,367.40</strong><span>+9.40 (+0.40%)</span><small>Sample series · not live</small></div>
          <div className="chart-wrap"><div className="y-labels"><span>2,370</span><span>2,350</span><span>2,330</span><span>2,310</span></div><svg viewBox="0 0 1000 210" preserveAspectRatio="none" role="img" aria-label="Illustrative XAUUSD price chart"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#35d6a0" stopOpacity=".22"/><stop offset="100%" stopColor="#35d6a0" stopOpacity="0"/></linearGradient></defs><path d={`M ${points.replaceAll(" ", " L ")} L 1000,210 L 0,210 Z`} fill="url(#area)"/><polyline points={points} fill="none" stroke="#35d6a0" strokeWidth="3" vectorEffect="non-scaling-stroke"/><line x1="0" y1="42" x2="1000" y2="42" stroke="#29343d" strokeDasharray="5 7"/></svg></div>
          <div className="chart-x"><span>09:00</span><span>10:00</span><span>11:00</span><span>12:00</span><span>13:00</span><span>14:00</span></div>
        </section>

        <div className="lower-grid">
          <section className="panel" id="strategies"><div className="panel-heading"><div><div className="eyebrow">RESEARCH ENGINE</div><h2>Strategy library</h2></div><span className="count">04 ACTIVE IN RESEARCH</span></div><div className="strategy-list">{strategies.map((strategy, index) => <div className="strategy-row" key={strategy.name}><div className="strategy-number">0{index + 1}</div><div className="strategy-name"><strong>{strategy.name}</strong><small>{strategy.type}</small></div><span className="research-tag">{strategy.status}</span></div>)}</div><p className="panel-note">Performance metrics appear after historical candles are loaded and backtests are run.</p></section>
          <section className="panel" id="regime"><div className="panel-heading"><div><div className="eyebrow">CONDITION DETECTION</div><h2>Market regimes</h2></div><span className="count">HEURISTIC V1</span></div><div className="regime-list"><div><span className="regime-symbol trend">↗</span><span><strong>Trending</strong><small>Directional movement</small></span><em>—</em></div><div><span className="regime-symbol range">↔</span><span><strong>Ranging</strong><small>Low directional efficiency</small></span><em>—</em></div><div><span className="regime-symbol vol">⌁</span><span><strong>High volatility</strong><small>Elevated candle range</small></span><em>—</em></div><div><span className="regime-symbol trans">◇</span><span><strong>Transition</strong><small>Unclear / mixed conditions</small></span><em>—</em></div></div><p className="panel-note">No strategy is automatically selected. Regime thresholds still require validation.</p></section>
        </div>

        <footer><span>XAUUSD AI COMMAND CENTRE</span><span>BUILD 0.1.0 · RESEARCH PREVIEW</span></footer>
      </section>
    </main>
  );
}
