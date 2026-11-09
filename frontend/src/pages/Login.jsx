import { useState } from "react";
import { useNavigate } from "react-router";
import "../login.css";
import { API_BASE_URL } from "../api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Login failed");
      navigate("/chat");
    } catch (err) {
      setError(err.message || "Unable to connect to server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-grain" aria-hidden="true" />
      <header className="login-topbar">
        <a className="login-brand" href="/" aria-label="Closer home">
          <span className="brand-symbol" aria-hidden="true"><i /><i /><i /></span>
          <span>closer<span className="brand-period">.</span></span>
        </a>
        <div className="login-top-note"><span className="status-dot" /> Your next conversation starts here</div>
      </header>

      <div className="login-layout">
        <section className="login-story" aria-label="Closer sales workspace">
          <div className="story-kicker"><span>THE CONVERSATION ADVANTAGE</span><span className="kicker-line" /></div>
          <h1>Make every<br />conversation <em>count.</em></h1>
          <p className="story-copy">The clarity to know what to say.<br />The confidence to close the deal.</p>

          <div className="insight-card">
            <div className="insight-head"><span className="insight-label"><span className="sparkle">✳</span> LIVE CONVERSATION INSIGHT</span><span className="live-indicator">LIVE</span></div>
            <div className="insight-rule" />
            <div className="insight-body">
              <div className="insight-avatar">JM</div>
              <div className="insight-person"><strong>Jordan Mitchell</strong><span>Head of Sales · Northstar</span></div>
              <div className="score"><strong>84</strong><span>LEAD SCORE</span></div>
            </div>
            <div className="insight-quote"><span className="quote-mark">“</span><span>We’re interested, but the timing isn’t quite right.</span></div>
            <div className="insight-footer"><span className="suggestion-icon">↗</span><span><b>Try reframing around their Q3 launch.</b><br />Connect the timeline to their stated priority.</span></div>
          </div>

          <div className="story-footer"><span className="story-stars">★★★★★</span><span>Built for the moments that move deals forward.</span></div>
        </section>

        <section className="login-panel" aria-labelledby="login-title">
          <div className="panel-eyebrow"><span className="panel-mark">✳</span> YOUR SALES WORKSPACE</div>
          <h2 id="login-title">Welcome back<span>.</span></h2>
          <p className="panel-subtitle">Pick up right where your best conversations begin.</p>

          <form className="login-form" onSubmit={handleSubmit}>
            <label htmlFor="login-email">Work email</label>
            <div className="field-wrap">
              <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="2.5" y="4" width="15" height="12" rx="2"/><path d="m3.5 5.5 6.5 5 6.5-5"/></svg>
              <input id="login-email" type="email" placeholder="you@company.com" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div className="password-label-row"><label htmlFor="login-password">Password</label><a href="mailto:support@closer.app?subject=Password%20reset">Forgot password?</a></div>
            <div className="field-wrap">
              <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3.5" y="8" width="13" height="9" rx="2"/><path d="M6.5 8V5.8a3.5 3.5 0 0 1 7 0V8M10 11v3"/></svg>
              <input id="login-password" type={showPassword ? "text" : "password"} placeholder="Enter your password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              <button className="password-toggle" type="button" onClick={() => setShowPassword((shown) => !shown)} aria-label={showPassword ? "Hide password" : "Show password"}>
                {showPassword ? "HIDE" : "SHOW"}
              </button>
            </div>

            {error && <p className="login-error" role="alert">{error}</p>}
            <button className="login-submit" type="submit" disabled={loading}>
              <span>{loading ? "Signing you in…" : "Sign in to your workspace"}</span><span className="submit-arrow" aria-hidden="true">↗</span>
            </button>
          </form>

          <div className="login-divider"><span /> <i>SECURE ACCESS</i> <span /></div>
          <p className="login-privacy"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2"/></svg> Your conversations and customer data stay private.</p>
          <p className="signup-prompt">New to Closer? <a href="mailto:support@closer.app?subject=Closer%20access">Talk to our team <span>↗</span></a></p>
        </section>
      </div>
      <footer className="login-bottom"><span>© 2025 CLOSER, INC.</span><div><a href="mailto:privacy@closer.app">PRIVACY</a><a href="mailto:legal@closer.app">TERMS</a></div><span className="bottom-location">MADE FOR THE MOMENT THAT MATTERS <b>✳</b></span></footer>
    </main>
  );
}

export default Login;
