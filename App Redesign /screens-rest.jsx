// ATTREQ — Wardrobe (2 variants), History, Profile, Location Permission, Loading

function WardrobeChips({ t, active = 'All' }) {
  const cats = ['All', 'Tops', 'Bottoms', 'Outer', 'Accents', 'Shoes'];
  return (
    <div style={{ display: 'flex', gap: 6, padding: '0 20px', overflowX: 'auto', marginTop: 18, marginBottom: 16 }}>
      {cats.map(c => {
        const isActive = c === active;
        return (
          <div key={c} style={{
            padding: '7px 14px', borderRadius: 999,
            background: isActive ? t.text : 'transparent',
            border: `1px solid ${isActive ? t.text : t.border}`,
            color: isActive ? t.bgDeep : t.textSec,
            fontFamily: FONT_MONO, fontSize: 10, letterSpacing: '0.18em',
            textTransform: 'uppercase', whiteSpace: 'nowrap',
            fontWeight: isActive ? 600 : 400,
          }}>{c}</div>
        );
      })}
    </div>
  );
}

// Variation A — Editorial masonry
function AttreqWardrobe({ t }) {
  const items = [
    { tone: 'top', label: 'Linen blouse', color: 'Bone', h: 220 },
    { tone: 'outer', label: 'Camel coat', color: 'Camel', h: 260 },
    { tone: 'bottom', label: 'Wide trouser', color: 'Charcoal', h: 240 },
    { tone: 'accent', label: 'Silk scarf', color: 'Rust', h: 180 },
    { tone: 'shoes', label: 'Leather boots', color: 'Black', h: 200 },
    { tone: 'top', label: 'Wool sweater', color: 'Moss', h: 230 },
    { tone: 'bag', label: 'Suede tote', color: 'Tan', h: 220 },
    { tone: 'bottom', label: 'Denim', color: 'Indigo', h: 250 },
  ];

  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflowY: 'auto', paddingBottom: 110 }}>
        <div style={{ padding: '0 24px' }}>
          <StatusSpacer/>
          <div style={{ paddingTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <MonoLabel style={{ color: t.textTer }}>Closet</MonoLabel>
              <div style={{ fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 36, color: t.text, marginTop: 8, lineHeight: 1, letterSpacing: '-0.02em' }}>Wardrobe</div>
              <div style={{ fontFamily: FONT_BODY, fontSize: 13, color: t.textSec, marginTop: 8 }}>
                <span style={{ color: t.gold }}>48 pieces</span> · last added Tuesday
              </div>
            </div>
            <div style={{
              width: 38, height: 38, borderRadius: 19,
              background: t.bgSurface, border: `1px solid ${t.borderSoft}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.textSec} strokeWidth="1.6">
                <circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>
              </svg>
            </div>
          </div>
        </div>

        <WardrobeChips t={t}/>

        {/* Add entry cards — prominent */}
        <div style={{ display: 'flex', gap: 10, padding: '0 20px', marginBottom: 22 }}>
          <div style={{
            flex: 1, padding: '14px 14px', borderRadius: 18,
            border: `1px dashed ${t.mossSoft}`,
            background: `linear-gradient(135deg, ${t.mossGlow}, transparent)`,
          }}>
            <div style={{ width: 28, height: 28, borderRadius: 14, background: t.moss, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F0EDE6" strokeWidth="1.8">
                <rect x="3" y="6" width="18" height="13" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M9 6l1.5-2h3L15 6"/>
              </svg>
            </div>
            <div style={{ fontFamily: FONT_DISPLAY, fontSize: 16, fontWeight: 600, color: t.text }}>Camera</div>
            <div style={{ fontFamily: FONT_BODY, fontSize: 11, color: t.textSec, marginTop: 2 }}>Capture a piece</div>
          </div>
          <div style={{
            flex: 1, padding: '14px 14px', borderRadius: 18,
            border: `1px dashed ${t.borderSoft}`,
            background: t.bgSurface,
          }}>
            <div style={{ width: 28, height: 28, borderRadius: 14, background: t.bgRaised, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.gold} strokeWidth="1.8">
                <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/>
              </svg>
            </div>
            <div style={{ fontFamily: FONT_DISPLAY, fontSize: 16, fontWeight: 600, color: t.text }}>Library</div>
            <div style={{ fontFamily: FONT_BODY, fontSize: 11, color: t.textSec, marginTop: 2 }}>From photos</div>
          </div>
        </div>

        {/* Masonry */}
        <div style={{ padding: '0 20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[items.slice(0, 4), items.slice(4)].map((col, ci) => (
            <div key={ci} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {col.map((it, i) => (
                <div key={i}>
                  <div style={{
                    height: it.h, borderRadius: 16, overflow: 'hidden',
                  }}>
                    <Garment tone={it.tone} t={t} ratio="auto" radius={16} style={{ height: '100%' }} mono={false}/>
                  </div>
                  <div style={{ paddingTop: 8, paddingLeft: 2 }}>
                    <div style={{ fontFamily: FONT_DISPLAY, fontSize: 14, fontWeight: 600, color: t.text, fontStyle: 'italic' }}>{it.label}</div>
                    <MonoLabel style={{ color: t.textTer, fontSize: 9 }}>{it.color}</MonoLabel>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <AttreqTabBar active="wardrobe" t={t}/>
    </PhoneBg>
  );
}

// Variation B — Even grid
function AttreqWardrobeGrid({ t }) {
  const items = [
    { tone: 'top', label: 'Linen blouse' },
    { tone: 'outer', label: 'Camel coat' },
    { tone: 'bottom', label: 'Wide trouser' },
    { tone: 'accent', label: 'Silk scarf' },
    { tone: 'shoes', label: 'Boots' },
    { tone: 'top', label: 'Wool knit' },
    { tone: 'bag', label: 'Suede tote' },
    { tone: 'bottom', label: 'Denim' },
    { tone: 'top', label: 'Cotton tee' },
  ];
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflowY: 'auto', paddingBottom: 110 }}>
        <div style={{ padding: '0 24px' }}>
          <StatusSpacer/>
          <div style={{ paddingTop: 14 }}>
            <MonoLabel style={{ color: t.textTer }}>48 pieces</MonoLabel>
            <div style={{ fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 36, color: t.text, marginTop: 8, letterSpacing: '-0.02em' }}>
              Your <span style={{ fontStyle: 'italic', color: t.gold }}>wardrobe</span>
            </div>
          </div>
        </div>

        <WardrobeChips t={t} active="Tops"/>

        {/* Image preview state — when an item is being uploaded */}
        <div style={{ margin: '0 20px 22px', borderRadius: 20, overflow: 'hidden', border: `1px solid ${t.goldSoft}`, position: 'relative' }}>
          <div style={{ height: 200 }}><Garment tone="outer" t={t} ratio="auto" radius={0} style={{ height: '100%' }} mono={false}/></div>
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(180deg, transparent 40%, rgba(13,18,16,0.85) 100%)',
          }}/>
          <div style={{ position: 'absolute', top: 12, left: 14 }}>
            <MonoLabel style={{ color: t.gold }}>Preview · uploading</MonoLabel>
          </div>
          <div style={{ position: 'absolute', bottom: 14, left: 14, right: 14, display: 'flex', gap: 8 }}>
            <button style={{ flex: 1, background: t.moss, border: 'none', color: '#F0EDE6', padding: '10px 0', borderRadius: 12, fontFamily: FONT_BODY, fontSize: 13, fontWeight: 600 }}>Upload</button>
            <button style={{ width: 90, background: 'rgba(0,0,0,0.4)', border: `1px solid ${t.borderSoft}`, color: t.text, padding: '10px 0', borderRadius: 12, fontFamily: FONT_BODY, fontSize: 13 }}>Discard</button>
          </div>
        </div>

        <div style={{ padding: '0 20px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
          {items.map((it, i) => (
            <div key={i} style={{ aspectRatio: '3/4', borderRadius: 12, overflow: 'hidden' }}>
              <Garment tone={it.tone} t={t} ratio="auto" radius={12} style={{ height: '100%' }} mono={false}/>
            </div>
          ))}
        </div>
      </div>
      <AttreqTabBar active="wardrobe" t={t}/>
    </PhoneBg>
  );
}

// History — timeline-style
function AttreqHistory({ t }) {
  const days = [
    { date: 'Yesterday', dateLine: 'MON · 04 · 24', items: [{ tones: ['top','bottom','accent'], label: 'Office Hours', score: 'Worn' }] },
    { date: 'Sunday', dateLine: 'SUN · 04 · 23', items: [{ tones: ['outer','bottom','shoes'], label: 'The Long Walk', score: 'Loved' }] },
    { date: 'Saturday', dateLine: 'SAT · 04 · 22', items: [{ tones: ['top','bottom','bag'], label: 'Cafe Sketch', score: 'Worn' }, { tones: ['outer','bottom','accent'], label: 'Quiet Evening', score: 'Skipped' }] },
  ];

  const ScorePill = ({ s }) => {
    const map = {
      'Worn':    { bg: t.mossSoft, fg: t.olive },
      'Loved':   { bg: t.goldSoft, fg: t.gold },
      'Skipped': { bg: 'transparent', fg: t.textTer, br: t.border },
    };
    const c = map[s];
    return (
      <span style={{
        padding: '3px 10px', borderRadius: 999,
        background: c.bg, border: c.br ? `1px solid ${c.br}` : 'none',
        fontFamily: FONT_MONO, fontSize: 9, letterSpacing: '0.18em',
        textTransform: 'uppercase', color: c.fg,
      }}>{s}</span>
    );
  };

  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflowY: 'auto', paddingBottom: 110 }}>
        <div style={{ padding: '0 24px' }}>
          <StatusSpacer/>
          <div style={{ paddingTop: 14 }}>
            <MonoLabel style={{ color: t.textTer }}>Diary</MonoLabel>
            <div style={{ fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 36, color: t.text, marginTop: 8, letterSpacing: '-0.02em' }}>History</div>
            <div style={{ fontFamily: FONT_BODY, fontSize: 13, color: t.textSec, marginTop: 6 }}>132 looks · 86 worn</div>
          </div>
        </div>

        <div style={{ padding: '24px 24px 0' }}>
          {days.map((day, di) => (
            <div key={di} style={{ marginBottom: 28 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 14 }}>
                <div style={{ fontFamily: FONT_DISPLAY, fontStyle: 'italic', fontSize: 20, color: t.text }}>{day.date}</div>
                <div style={{ flex: 1, height: 1, background: t.borderSoft }}/>
                <MonoLabel style={{ color: t.textTer }}>{day.dateLine}</MonoLabel>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {day.items.map((it, ii) => (
                  <div key={ii} style={{
                    background: t.bgSurface, borderRadius: 18, padding: 14,
                    border: `1px solid ${t.borderSoft}`,
                    display: 'flex', gap: 12,
                  }}>
                    <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                      {it.tones.map((tn, ti) => (
                        <div key={ti} style={{ width: 46, height: 60 }}>
                          <Garment tone={tn} t={t} ratio="auto" radius={8} style={{ height: '100%' }} mono={false}/>
                        </div>
                      ))}
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minWidth: 0 }}>
                      <div>
                        <div style={{ fontFamily: FONT_DISPLAY, fontSize: 17, fontWeight: 600, color: t.text, fontStyle: 'italic' }}>{it.label}</div>
                        <MonoLabel style={{ color: t.textTer, fontSize: 9 }}>3 pieces</MonoLabel>
                      </div>
                      <div><ScorePill s={it.score}/></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <AttreqTabBar active="history" t={t}/>
    </PhoneBg>
  );
}

// Profile
function AttreqProfile({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', overflowY: 'auto', paddingBottom: 110 }}>
        <div style={{ padding: '0 24px' }}>
          <StatusSpacer/>
          <div style={{ paddingTop: 14 }}>
            <MonoLabel style={{ color: t.textTer }}>You</MonoLabel>
            <div style={{ fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 36, color: t.text, marginTop: 8, letterSpacing: '-0.02em' }}>Profile</div>
          </div>

          {/* Identity card — editorial */}
          <div style={{
            marginTop: 22, padding: 20, borderRadius: 22,
            background: `linear-gradient(180deg, ${t.bgSurface}, ${t.bgRaised})`,
            border: `1px solid ${t.borderSoft}`,
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', top: 0, left: 16, right: 16, height: 2,
              background: t.gold, borderRadius: '0 0 2px 2px',
            }}/>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 56, height: 56, borderRadius: 28,
                background: `linear-gradient(135deg, ${t.gold}, ${t.olive})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600,
                color: t.bgDeep, fontStyle: 'italic',
              }}>IA</div>
              <div>
                <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, fontWeight: 600, color: t.text }}>Iris Andersen</div>
                <div style={{ fontFamily: FONT_BODY, fontSize: 12.5, color: t.textSec, marginTop: 2 }}>iris@attreq.app</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 24, marginTop: 18, paddingTop: 16, borderTop: `1px solid ${t.borderSoft}` }}>
              <div>
                <MonoLabel style={{ color: t.textTer }}>Pieces</MonoLabel>
                <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, color: t.text, marginTop: 2 }}>48</div>
              </div>
              <div>
                <MonoLabel style={{ color: t.textTer }}>Worn</MonoLabel>
                <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, color: t.text, marginTop: 2 }}>86</div>
              </div>
              <div>
                <MonoLabel style={{ color: t.textTer }}>Streak</MonoLabel>
                <div style={{ fontFamily: FONT_DISPLAY, fontSize: 22, color: t.gold, marginTop: 2, fontStyle: 'italic' }}>12d</div>
              </div>
            </div>
          </div>
        </div>

        {/* Settings sections */}
        <div style={{ padding: '24px 24px 0' }}>
          <MonoLabel style={{ color: t.textTer, marginBottom: 12, display: 'block' }}>Preferences</MonoLabel>
          <div style={{ background: t.bgSurface, borderRadius: 18, border: `1px solid ${t.borderSoft}`, overflow: 'hidden' }}>
            {[
              { title: 'Brooklyn, NY', sub: '40.6782°N · 73.9442°W', icon: 'pin' },
              { title: 'Daily reminder', sub: '8:00 AM · weekdays', tail: 'on' },
              { title: 'Style preferences', sub: 'Minimal · earthy · layered', tail: 'edit' },
            ].map((row, i) => (
              <div key={i} style={{
                padding: '16px 18px',
                borderBottom: i < 2 ? `1px solid ${t.borderSoft}` : 'none',
                display: 'flex', alignItems: 'center', gap: 14,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: FONT_BODY, fontSize: 15, color: t.text }}>{row.title}</div>
                  <MonoLabel style={{ color: t.textTer, marginTop: 3, display: 'block' }}>{row.sub}</MonoLabel>
                </div>
                {row.tail === 'on' && (
                  <div style={{ width: 38, height: 22, borderRadius: 11, background: t.moss, position: 'relative', display: 'flex', alignItems: 'center' }}>
                    <div style={{ width: 18, height: 18, borderRadius: 9, background: '#F0EDE6', marginLeft: 18 }}/>
                  </div>
                )}
                {row.tail === 'edit' && (
                  <MonoLabel style={{ color: t.gold }}>Edit</MonoLabel>
                )}
                {!row.tail && (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.textTer} strokeWidth="1.8"><path d="M9 6l6 6-6 6"/></svg>
                )}
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 24, textAlign: 'center',
            fontFamily: FONT_MONO, fontSize: 10, letterSpacing: '0.2em',
            textTransform: 'uppercase', color: t.clay,
            padding: '14px 0', opacity: 0.85,
          }}>Sign out</div>
          <div style={{
            textAlign: 'center', fontFamily: FONT_MONO, fontSize: 9, letterSpacing: '0.18em',
            color: t.textTer, opacity: 0.6, marginTop: 4,
          }}>v 1.4.2 · ATTREQ</div>
        </div>
      </div>
      <AttreqTabBar active="profile" t={t}/>
    </PhoneBg>
  );
}

// Location permission (first-run)
function AttreqLocation({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '0 28px' }}>
        <StatusSpacer/>
        <div style={{ paddingTop: 14 }}>
          <MonoLabel style={{ color: t.textTer }}>Step 02</MonoLabel>
        </div>

        {/* Compass-like illustration */}
        <div style={{ marginTop: 50, alignSelf: 'center', position: 'relative', width: 180, height: 180 }}>
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            border: `1px solid ${t.borderSoft}`,
            background: `radial-gradient(circle at 50% 50%, ${t.mossGlow}, transparent 70%)`,
          }}/>
          <div style={{
            position: 'absolute', inset: 30, borderRadius: '50%',
            border: `1px dashed ${t.mossSoft}`,
          }}/>
          <div style={{
            position: 'absolute', inset: 60, borderRadius: '50%',
            background: t.moss,
            boxShadow: `0 0 32px ${t.mossSoft}, inset 0 0 12px rgba(0,0,0,0.3)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F0EDE6" strokeWidth="1.5" strokeLinecap="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
          {/* compass marks */}
          {['N','E','S','W'].map((d, i) => (
            <div key={d} style={{
              position: 'absolute', top: '50%', left: '50%',
              transform: `translate(-50%, -50%) rotate(${i*90}deg) translateY(-95px) rotate(${-i*90}deg)`,
              fontFamily: FONT_MONO, fontSize: 9, letterSpacing: '0.15em', color: t.textTer,
            }}>{d}</div>
          ))}
        </div>

        <div style={{ marginTop: 50, textAlign: 'center' }}>
          <div style={{
            fontFamily: FONT_DISPLAY, fontSize: 30, fontWeight: 600,
            color: t.text, lineHeight: 1.15, letterSpacing: '-0.02em',
          }}>The weather decides<br/><span style={{ fontStyle: 'italic', color: t.gold }}>before you do.</span></div>
          <div style={{
            fontFamily: FONT_BODY, fontSize: 14, color: t.textSec,
            marginTop: 18, lineHeight: 1.55, maxWidth: 300, marginLeft: 'auto', marginRight: 'auto',
          }}>Share your location and we'll pair tomorrow's looks to tomorrow's sky — never wool on a warm day, never silk in the rain.</div>
        </div>

        <div style={{ flex: 1 }}/>

        <div style={{ paddingBottom: 38 }}>
          <button style={{
            width: '100%', background: t.gold, color: '#1A1410', border: 'none',
            fontFamily: FONT_BODY, fontSize: 15, fontWeight: 600,
            padding: '16px 0', borderRadius: 16,
          }}>Allow location access</button>
          <div style={{
            textAlign: 'center', marginTop: 14,
            fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.2em',
            textTransform: 'uppercase', color: t.textTer,
          }}>Maybe later</div>
        </div>
      </div>
    </PhoneBg>
  );
}

// Loading skeleton
function AttreqLoading({ t }) {
  const Shim = ({ h, w = '100%', r = 12 }) => (
    <div style={{ height: h, width: w, borderRadius: r, background: t.bgSurface, position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `linear-gradient(90deg, transparent, ${t.bgRaised}, transparent)`,
        animation: 'attreqShim 1.6s ease-in-out infinite',
      }}/>
    </div>
  );
  return (
    <PhoneBg t={t}>
      <style>{`@keyframes attreqShim { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }`}</style>
      <div style={{ height: '100%', overflow: 'hidden', padding: '0 24px' }}>
        <StatusSpacer/>
        <div style={{ paddingTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Shim h={12} w="40%" r={6}/>
          <Shim h={32} w="65%" r={8}/>
        </div>
        <div style={{ marginTop: 28, height: 64, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
          <Shim h={64}/><Shim h={64}/><Shim h={64}/>
        </div>
        <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ background: t.bgSurface, borderRadius: 22, padding: 14, border: `1px solid ${t.borderSoft}` }}>
            <Shim h={10} w="35%" r={5}/>
            <div style={{ height: 10 }}/>
            <Shim h={20} w="55%" r={6}/>
            <div style={{ height: 14 }}/>
            <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 8, height: 220 }}>
              <Shim h="100%" r={14}/>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Shim h="100%" r={14}/><Shim h="100%" r={14}/>
              </div>
            </div>
          </div>
        </div>
      </div>
      <AttreqTabBar active="today" t={t}/>
    </PhoneBg>
  );
}

// First suggestion celebration
function AttreqCelebrate({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 50% 30%, ${t.goldSoft}, transparent 60%)`, pointerEvents: 'none' }}/>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '0 28px' }}>
        <StatusSpacer/>
        <div style={{ paddingTop: 14 }}>
          <MonoLabel style={{ color: t.gold }}>A first.</MonoLabel>
        </div>

        <div style={{ marginTop: 36, textAlign: 'center' }}>
          <div style={{
            fontFamily: FONT_DISPLAY, fontStyle: 'italic', fontSize: 14,
            color: t.gold, letterSpacing: '0.05em',
          }}>Look No. 01</div>
          <div style={{
            fontFamily: FONT_DISPLAY, fontSize: 32, fontWeight: 600,
            color: t.text, marginTop: 8, lineHeight: 1.1, letterSpacing: '-0.02em',
          }}>Your first<br/><span style={{ fontStyle: 'italic', color: t.gold }}>composed look.</span></div>
        </div>

        <div style={{
          marginTop: 32, alignSelf: 'center',
          position: 'relative', width: 240, height: 320,
        }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: 150, height: 200, transform: 'rotate(-4deg)', boxShadow: '0 12px 28px rgba(0,0,0,0.4)' }}>
            <Garment tone="top" t={t} ratio="auto" radius={10} style={{ height: '100%' }} mono={false}/>
          </div>
          <div style={{ position: 'absolute', top: 80, right: 0, width: 130, height: 180, transform: 'rotate(6deg)', boxShadow: '0 12px 28px rgba(0,0,0,0.4)' }}>
            <Garment tone="bottom" t={t} ratio="auto" radius={10} style={{ height: '100%' }} mono={false}/>
          </div>
          <div style={{ position: 'absolute', bottom: 10, left: 60, width: 90, height: 110, transform: 'rotate(-2deg)', boxShadow: '0 12px 28px rgba(0,0,0,0.4)' }}>
            <Garment tone="accent" t={t} ratio="auto" radius={10} style={{ height: '100%' }} mono={false}/>
          </div>
        </div>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <div style={{ fontFamily: FONT_DISPLAY, fontStyle: 'italic', fontSize: 22, color: t.text }}>The Long Walk</div>
          <div style={{ fontFamily: FONT_BODY, fontSize: 13, color: t.textSec, marginTop: 8, maxWidth: 280, margin: '8px auto 0', lineHeight: 1.5 }}>
            From now on, every morning gets a few of these — calmer than choosing, smarter than chance.
          </div>
        </div>

        <div style={{ flex: 1 }}/>

        <div style={{ paddingBottom: 38 }}>
          <button style={{
            width: '100%', background: t.moss, color: '#F0EDE6', border: 'none',
            fontFamily: FONT_BODY, fontSize: 15, fontWeight: 600,
            padding: '16px 0', borderRadius: 16,
            boxShadow: `0 8px 20px rgba(54,102,74,0.32)`,
          }}>Wear this today</button>
        </div>
      </div>
    </PhoneBg>
  );
}

Object.assign(window, { AttreqWardrobe, AttreqWardrobeGrid, AttreqHistory, AttreqProfile, AttreqLocation, AttreqLoading, AttreqCelebrate });
