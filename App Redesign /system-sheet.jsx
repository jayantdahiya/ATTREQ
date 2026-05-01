// ATTREQ — Design System sheet (compressed inside an artboard)
// Renders typography, color, components, motion notes.

function AttreqSystemSheet({ t, mode = 'dark' }) {
  return (
    <div style={{
      width: '100%', height: '100%',
      background: t.bgDeep, color: t.text,
      fontFamily: FONT_BODY, padding: 32, overflow: 'auto', position: 'relative',
    }}>
      <div style={{
        position: 'absolute', inset: 0, backgroundImage: GRAIN_URL,
        backgroundSize: '220px 220px', opacity: 0.4, pointerEvents: 'none', mixBlendMode: 'overlay',
      }}/>
      <div style={{ position: 'relative' }}>
        <MonoLabel style={{ color: t.textTer }}>{mode.toUpperCase()} · Design System</MonoLabel>
        <div style={{ fontFamily: FONT_DISPLAY, fontSize: 44, fontWeight: 600, color: t.text, marginTop: 10, letterSpacing: '-0.02em' }}>
          ATTREQ — <span style={{ fontStyle: 'italic', color: t.gold }}>system</span>
        </div>
        <div style={{ fontFamily: FONT_BODY, fontSize: 13, color: t.textSec, marginTop: 6, maxWidth: 420 }}>Editorial utility · earthy palette · serif × sans × mono</div>

        {/* Type */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Typography</MonoLabel>
          <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr', gap: 12 }}>
            <div><MonoLabel style={{ color: t.textTer }}>Display · Cormorant 32 / -0.5</MonoLabel><div style={{ fontFamily: FONT_DISPLAY, fontSize: 32, fontWeight: 600, marginTop: 2 }}>Your closet, <span style={{ fontStyle: 'italic', color: t.gold }}>curated</span>.</div></div>
            <div><MonoLabel style={{ color: t.textTer }}>H1 · 28</MonoLabel><div style={{ fontFamily: FONT_DISPLAY, fontSize: 28, fontWeight: 600, marginTop: 2 }}>Today's looks</div></div>
            <div><MonoLabel style={{ color: t.textTer }}>H2 · 22</MonoLabel><div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600, fontStyle: 'italic', marginTop: 2 }}>The Long Walk</div></div>
            <div><MonoLabel style={{ color: t.textTer }}>Body · DM Sans 16</MonoLabel><div style={{ fontFamily: FONT_BODY, fontSize: 16, marginTop: 2, color: t.textSec }}>Wool sweater, charcoal trouser, suede boot.</div></div>
            <div><MonoLabel style={{ color: t.textTer }}>Mono · IBM Plex 11 / 1.5 tracking</MonoLabel><div style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', marginTop: 4, color: t.text }}>52° · OVERCAST · LAYERED</div></div>
          </div>
        </div>

        {/* Color */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Palette</MonoLabel>
          <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
            {[
              ['Moss', t.moss], ['Olive', t.olive], ['Gold', t.gold], ['Clay', t.clay],
              ['bgDeep', t.bgDeep], ['bgSurface', t.bgSurface], ['bgRaised', t.bgRaised], ['Border', t.border],
            ].map(([name, c]) => (
              <div key={name}>
                <div style={{ height: 60, borderRadius: 10, background: c, border: `1px solid ${t.borderSoft}` }}/>
                <MonoLabel style={{ color: t.textTer, marginTop: 6, display: 'block' }}>{name}</MonoLabel>
                <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: t.textSec, marginTop: 2 }}>{c}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Components — buttons */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Buttons</MonoLabel>
          <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button style={{ background: t.moss, color: '#F0EDE6', border: 'none', padding: '12px 22px', borderRadius: 14, fontFamily: FONT_BODY, fontWeight: 600, fontSize: 13, boxShadow: `0 4px 12px rgba(54,102,74,0.32)` }}>Primary</button>
            <button style={{ background: t.gold, color: '#1A1410', border: 'none', padding: '12px 22px', borderRadius: 14, fontFamily: FONT_BODY, fontWeight: 600, fontSize: 13 }}>Premium</button>
            <button style={{ background: 'transparent', color: t.text, border: `1px solid ${t.border}`, padding: '12px 22px', borderRadius: 14, fontFamily: FONT_BODY, fontSize: 13 }}>Secondary</button>
            <button style={{ background: 'transparent', color: t.textSec, border: 'none', padding: '12px 22px', fontFamily: FONT_MONO, fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase' }}>Ghost</button>
            <button style={{ background: 'transparent', color: t.clay, border: `1px solid ${t.clay}`, padding: '12px 22px', borderRadius: 14, fontFamily: FONT_BODY, fontSize: 13 }}>Danger</button>
          </div>
        </div>

        {/* Cards */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Cards</MonoLabel>
          <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
            {[
              { name: 'Default', bg: t.bgSurface },
              { name: 'Elevated', bg: t.bgRaised },
              { name: 'Outlined', bg: 'transparent' },
              { name: 'Premium', bg: t.bgSurface, gold: true },
            ].map(c => (
              <div key={c.name} style={{ background: c.bg, border: `1px solid ${t.borderSoft}`, borderRadius: 18, padding: 14, height: 90, position: 'relative', overflow: 'hidden' }}>
                {c.gold && <div style={{ position: 'absolute', top: 0, left: 14, right: 14, height: 2, background: t.gold }}/>}
                <MonoLabel style={{ color: t.textTer }}>{c.name}</MonoLabel>
                <div style={{ fontFamily: FONT_DISPLAY, fontSize: 17, color: t.text, marginTop: 8, fontStyle: 'italic' }}>Sample</div>
              </div>
            ))}
          </div>
        </div>

        {/* Badges */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Badges & inputs</MonoLabel>
          <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ padding: '4px 10px', borderRadius: 999, background: t.mossSoft, color: t.olive, fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.18em', textTransform: 'uppercase' }}>Worn</span>
            <span style={{ padding: '4px 10px', borderRadius: 999, background: t.goldSoft, color: t.gold, fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.18em', textTransform: 'uppercase' }}>Loved</span>
            <span style={{ padding: '4px 10px', borderRadius: 999, border: `1px solid ${t.border}`, color: t.textTer, fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.18em', textTransform: 'uppercase' }}>Skipped</span>
          </div>

          <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
            <div>
              <MonoLabel style={{ color: t.textTer }}>Default</MonoLabel>
              <div style={{ borderBottom: `1px solid ${t.border}`, paddingBottom: 8, marginTop: 6, color: t.textTer }}>Email</div>
            </div>
            <div>
              <MonoLabel style={{ color: t.gold }}>Focused</MonoLabel>
              <div style={{ borderBottom: `1px solid ${t.gold}`, paddingBottom: 8, marginTop: 6, color: t.text }}>iris@attreq.app</div>
            </div>
            <div>
              <MonoLabel style={{ color: t.clay }}>Error</MonoLabel>
              <div style={{ borderBottom: `1px solid ${t.clay}`, paddingBottom: 8, marginTop: 6, color: t.text }}>iris@</div>
            </div>
          </div>
        </div>

        {/* Motion */}
        <div style={{ marginTop: 28, paddingTop: 20, borderTop: `1px solid ${t.borderSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Motion</MonoLabel>
          <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, fontFamily: FONT_BODY, fontSize: 12, color: t.textSec, lineHeight: 1.5 }}>
            <div><b style={{ color: t.text, fontWeight: 600 }}>Card press</b> — scale 1 → 0.97, spring (220, 26, 1)</div>
            <div><b style={{ color: t.text, fontWeight: 600 }}>List entry</b> — stagger 80ms, fade + Y 12px, ease-out 320ms</div>
            <div><b style={{ color: t.text, fontWeight: 600 }}>Pull-refresh</b> — golden thread weaves through wordmark, dissolves into cards</div>
            <div><b style={{ color: t.text, fontWeight: 600 }}>Tab switch</b> — content cross-fade 200ms, no horizontal slide</div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { AttreqSystemSheet });
