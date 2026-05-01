// ATTREQ — Tab bar variations + Pull-to-refresh + Design system sheet

function TabBarVariantArtboard({ t, variant }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', position: 'relative', padding: '0 24px' }}>
        <StatusSpacer/>
        <div style={{ paddingTop: 14 }}>
          <MonoLabel style={{ color: t.textTer }}>Tab bar — {variant}</MonoLabel>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 26, color: t.text, marginTop: 10, fontStyle: 'italic' }}>Navigation study</div>
        </div>

        {/* sample content blocks */}
        <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[180, 100, 140].map((h, i) => (
            <div key={i} style={{ height: h, background: t.bgSurface, borderRadius: 16, border: `1px solid ${t.borderSoft}` }}/>
          ))}
        </div>
      </div>
      <AttreqTabBar active="today" t={t} variant={variant === 'edge' ? 'edge' : 'floating'}/>
    </PhoneBg>
  );
}

// Pull-to-refresh moment — fabric thread metaphor
function AttreqPullRefresh({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflow: 'hidden', position: 'relative' }}>
        <StatusSpacer/>

        {/* Pull indicator: thread woven into "ATTREQ" */}
        <div style={{ height: 110, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
          <svg width="80" height="40" viewBox="0 0 80 40" fill="none">
            <path d="M5 20 Q 15 5, 25 20 T 45 20 T 65 20 T 75 20" stroke={t.gold} strokeWidth="1.4" strokeLinecap="round"/>
            <circle cx="75" cy="20" r="3" fill={t.gold}/>
          </svg>
          <MonoLabel style={{ color: t.gold }}>Weaving today's looks…</MonoLabel>
        </div>

        {/* Pushed-down content peek */}
        <div style={{ padding: '0 24px', opacity: 0.6 }}>
          <MonoLabel style={{ color: t.textTer }}>Tuesday · 04 · 25</MonoLabel>
          <div style={{
            fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 32,
            color: t.text, marginTop: 10, letterSpacing: '-0.02em',
          }}>Good morning,<br/><span style={{ fontStyle: 'italic', color: t.gold }}>Iris.</span></div>
          <div style={{ marginTop: 24, height: 200, background: t.bgSurface, borderRadius: 18, border: `1px solid ${t.borderSoft}` }}/>
        </div>

        {/* Annotation */}
        <div style={{ position: 'absolute', bottom: 110, left: 24, right: 24, padding: 14, background: t.bgSurface, borderRadius: 16, border: `1px solid ${t.goldSoft}` }}>
          <MonoLabel style={{ color: t.gold }}>Motion note</MonoLabel>
          <div style={{ fontFamily: FONT_BODY, fontSize: 12.5, color: t.textSec, marginTop: 6, lineHeight: 1.45 }}>
            Pull down → a single golden thread sews itself across "ATTREQ". On release, threads dissolve into new look cards (stagger 80ms · spring tension 220, friction 26).
          </div>
        </div>
      </div>
      <AttreqTabBar active="today" t={t}/>
    </PhoneBg>
  );
}

Object.assign(window, { TabBarVariantArtboard, AttreqPullRefresh });
