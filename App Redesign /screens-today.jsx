// ATTREQ — Today (Dashboard) — 3 layout variations
// Common header + outfit cards in different compositions.

function TodayHeader({ t }) {
  return (
    <div style={{ padding: '0 24px' }}>
      <StatusSpacer/>
      <div style={{ paddingTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <MonoLabel style={{ color: t.textTer }}>Tuesday · 04 · 25</MonoLabel>
          <div style={{
            fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 36,
            color: t.text, lineHeight: 1, marginTop: 10, letterSpacing: '-0.02em',
          }}>Good morning,<br/><span style={{ fontStyle: 'italic', color: t.gold }}>Iris.</span></div>
        </div>
        <div style={{
          width: 38, height: 38, borderRadius: 19,
          background: t.bgSurface, border: `1px solid ${t.borderSoft}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.textSec} strokeWidth="1.8">
            <path d="M3 12h18M3 6h18M3 18h12"/>
          </svg>
        </div>
      </div>

      {/* Weather strip — marginalia, not a widget */}
      <div style={{
        marginTop: 22, display: 'flex', gap: 0, alignItems: 'baseline',
        borderTop: `1px solid ${t.borderSoft}`,
        borderBottom: `1px solid ${t.borderSoft}`,
        padding: '12px 0',
      }}>
        <div style={{ flex: 1 }}>
          <MonoLabel style={{ color: t.textTer }}>Brooklyn</MonoLabel>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, color: t.text, fontWeight: 500, marginTop: 2 }}>52°</div>
        </div>
        <div style={{ flex: 1 }}>
          <MonoLabel style={{ color: t.textTer }}>Sky</MonoLabel>
          <div style={{ fontFamily: FONT_BODY, fontSize: 14, color: t.text, marginTop: 4 }}>Overcast, light rain pm</div>
        </div>
        <div style={{ width: 60, textAlign: 'right' }}>
          <MonoLabel style={{ color: t.textTer }}>Feel</MonoLabel>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 16, color: t.olive, marginTop: 4, fontStyle: 'italic' }}>Crisp</div>
        </div>
      </div>
    </div>
  );
}

function ActionRow({ t }) {
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
      <button style={{
        flex: 1, background: t.moss, border: 'none', color: '#F0EDE6',
        fontFamily: FONT_BODY, fontSize: 13.5, fontWeight: 600,
        padding: '13px 0', borderRadius: 14,
        letterSpacing: '0.04em',
        boxShadow: `0 4px 12px rgba(54,102,74,0.28)`,
      }}>Wear this</button>
      <button style={{
        width: 50, background: 'transparent', border: `1px solid ${t.border}`,
        borderRadius: 14, padding: '12px 0', color: t.textSec,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
        </svg>
      </button>
      <button style={{
        width: 50, background: 'transparent', border: `1px solid ${t.border}`,
        borderRadius: 14, padding: '12px 0', color: t.textTer,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M5 12h14"/>
        </svg>
      </button>
    </div>
  );
}

// Variation A — Editorial collage (top large, bottom medium, accent small)
function OutfitCardA({ t, idx = 1, label = 'The Long Walk' }) {
  return (
    <div style={{
      background: t.bgSurface,
      borderRadius: 24,
      padding: 16,
      border: `1px solid ${t.borderSoft}`,
      boxShadow: `0 8px 24px rgba(0,0,0,0.18)`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <div>
          <MonoLabel style={{ color: t.gold }}>Look No. 0{idx}</MonoLabel>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600, color: t.text, fontStyle: 'italic', marginTop: 2 }}>{label}</div>
        </div>
        <MonoLabel style={{ color: t.textTer }}>92% match</MonoLabel>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 8, height: 280 }}>
        <Garment tone="top" label="Top · Wool" t={t} ratio="auto" style={{ height: '100%' }}/>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Garment tone="bottom" label="Bottom" t={t} ratio="auto" style={{ flex: 1.6 }}/>
          <Garment tone="accent" label="Accent" t={t} ratio="auto" style={{ flex: 1 }}/>
        </div>
      </div>

      <div style={{
        display: 'flex', gap: 14, marginTop: 14,
        fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.15em',
        color: t.textTer, textTransform: 'uppercase',
      }}>
        <span>52° · OVERCAST</span>
        <span style={{ color: t.olive }}>· LAYERED</span>
        <span>· WORN 2× THIS MONTH</span>
      </div>

      <ActionRow t={t}/>
    </div>
  );
}

// Variation B — Vertical stack with floating accent inset
function OutfitCardB({ t, idx = 2, label = 'Office Hours' }) {
  return (
    <div style={{
      background: t.bgSurface,
      borderRadius: 24,
      padding: 16,
      border: `1px solid ${t.borderSoft}`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <div>
          <MonoLabel style={{ color: t.gold }}>Look No. 0{idx}</MonoLabel>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600, color: t.text, fontStyle: 'italic', marginTop: 2 }}>{label}</div>
        </div>
        <MonoLabel style={{ color: t.textTer }}>87%</MonoLabel>
      </div>

      <div style={{ position: 'relative' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <Garment tone="outer" label="Outer · Linen" t={t} ratio="16/9" radius={18}/>
          <Garment tone="bottom" label="Bottom · Trouser" t={t} ratio="16/9" radius={18}/>
        </div>
        {/* Accent inset, top-right */}
        <div style={{ position: 'absolute', top: 12, right: 12, width: 80, height: 80,
          borderRadius: 12, overflow: 'hidden',
          boxShadow: `0 8px 18px rgba(0,0,0,0.4), 0 0 0 3px ${t.bgSurface}`,
        }}>
          <Garment tone="accent" label="Acc." t={t} ratio="auto" style={{ height: '100%' }} radius={12}/>
        </div>
      </div>

      <div style={{
        display: 'flex', gap: 14, marginTop: 12,
        fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.15em',
        color: t.textTer, textTransform: 'uppercase',
      }}>
        <span>52°</span><span>· INDOOR DAY</span><span style={{ color: t.olive }}>· NEW PAIRING</span>
      </div>

      <ActionRow t={t}/>
    </div>
  );
}

// Variation C — Magazine spread (top spans, bottom + accent split)
function OutfitCardC({ t, idx = 3, label = 'The Quiet Evening' }) {
  return (
    <div style={{
      background: t.bgSurface,
      borderRadius: 24,
      overflow: 'hidden',
      border: `1px solid ${t.borderSoft}`,
    }}>
      <div style={{ height: 200, position: 'relative' }}>
        <Garment tone="top" label="" t={t} ratio="auto" radius={0} style={{ height: '100%' }}/>
        <div style={{
          position: 'absolute', bottom: 12, left: 16,
        }}>
          <MonoLabel style={{ color: '#D4A854' }}>Look No. 0{idx}</MonoLabel>
          <div style={{
            fontFamily: FONT_DISPLAY, fontSize: 26, color: '#F0EDE6',
            fontStyle: 'italic', fontWeight: 600, marginTop: 4,
          }}>{label}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: t.borderSoft }}>
        <div style={{ background: t.bgSurface, padding: '10px 14px' }}>
          <Garment tone="bottom" label="Bottom" t={t} ratio="3/4" radius={10}/>
        </div>
        <div style={{ background: t.bgSurface, padding: '10px 14px' }}>
          <Garment tone="accent" label="Accent" t={t} ratio="3/4" radius={10}/>
        </div>
      </div>

      <div style={{ padding: '12px 16px 16px' }}>
        <div style={{
          display: 'flex', gap: 14, marginBottom: 10,
          fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.15em',
          color: t.textTer, textTransform: 'uppercase',
        }}>
          <span>52° · DUSK</span><span style={{ color: t.olive }}>· DINNER</span>
        </div>
        <ActionRow t={t}/>
      </div>
    </div>
  );
}

function AttreqToday({ t, variant = 'A' }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflowY: 'auto', paddingBottom: 110 }}>
        <TodayHeader t={t}/>

        <div style={{ padding: '20px 24px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <div style={{ fontFamily: FONT_DISPLAY, fontSize: 18, color: t.text, fontStyle: 'italic' }}>Today's looks</div>
          <MonoLabel style={{ color: t.textTer }}>3 of 12</MonoLabel>
        </div>

        <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {variant === 'A' && (<>
            <OutfitCardA t={t} idx={1} label="The Long Walk"/>
            <OutfitCardB t={t} idx={2} label="Office Hours"/>
            <OutfitCardC t={t} idx={3} label="Quiet Evening"/>
          </>)}
          {variant === 'B' && (<>
            <OutfitCardB t={t} idx={1} label="Office Hours"/>
            <OutfitCardB t={t} idx={2} label="Cafe Sketch"/>
            <OutfitCardB t={t} idx={3} label="The Long Walk"/>
          </>)}
          {variant === 'C' && (<>
            <OutfitCardC t={t} idx={1} label="Quiet Evening"/>
            <OutfitCardC t={t} idx={2} label="Studio Day"/>
          </>)}
        </div>
      </div>

      <AttreqTabBar active="today" t={t}/>
    </PhoneBg>
  );
}

// Today empty state — no wardrobe yet
function AttreqTodayEmpty({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '0 28px' }}>
        <StatusSpacer/>
        <div style={{ paddingTop: 14 }}>
          <MonoLabel style={{ color: t.textTer }}>Tuesday · 04 · 25</MonoLabel>
          <div style={{
            fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 32,
            color: t.text, marginTop: 10, lineHeight: 1.05,
          }}>Good morning,<br/><span style={{ fontStyle: 'italic', color: t.gold }}>Iris.</span></div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', paddingBottom: 100 }}>
          {/* Empty illustration: stacked rectangles suggesting folded clothes */}
          <div style={{ alignSelf: 'center', display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 30, opacity: 0.5 }}>
            {[1,2,3].map(i => (
              <div key={i} style={{
                width: 120 - i*8, height: 16,
                background: t.bgSurface, borderRadius: 4,
                border: `1px solid ${t.borderSoft}`,
                marginLeft: i*4,
              }}/>
            ))}
          </div>

          <div style={{
            fontFamily: FONT_DISPLAY, fontSize: 26, fontStyle: 'italic',
            color: t.text, textAlign: 'center', lineHeight: 1.3,
            marginBottom: 12,
          }}>An empty closet,<br/>a quiet morning.</div>
          <div style={{
            fontFamily: FONT_BODY, fontSize: 14, color: t.textSec,
            textAlign: 'center', maxWidth: 280, alignSelf: 'center', lineHeight: 1.55,
          }}>Add a few favorites and we'll start composing looks. Five pieces is enough to begin.</div>

          <button style={{
            marginTop: 28, alignSelf: 'center',
            background: t.gold, color: '#1A1410', border: 'none',
            fontFamily: FONT_BODY, fontSize: 14, fontWeight: 600,
            padding: '14px 28px', borderRadius: 14,
          }}>Add your first piece →</button>
        </div>
      </div>
      <AttreqTabBar active="today" t={t}/>
    </PhoneBg>
  );
}

Object.assign(window, { AttreqToday, AttreqTodayEmpty, OutfitCardA, OutfitCardB, OutfitCardC });
