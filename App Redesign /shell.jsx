// ATTREQ — Phone shell with status bar + tab bar + grain
// Each Screen component returns a self-contained app surface fitting an iPhone 15 Pro frame
// (393×852pt) but rendered into IOSDevice (402×874).

const SCREEN_W = 402;
const SCREEN_H = 874;
// Available content area between status bar (top ~54) and home indicator (bottom 34)
const SAFE_TOP = 54;
const SAFE_BOTTOM = 34;

// Custom status bar overlay matching app bg (no IOSDevice nav). We always
// render the IOSDevice's own status bar though — this is just the spacer.
function StatusSpacer() {
  return <div style={{ height: SAFE_TOP }}/>;
}

// Lightweight tab bar — floating moss-tinted island with 4 tabs.
function AttreqTabBar({ active = 'today', t, variant = 'floating' }) {
  const tabs = [
    { id: 'today', label: 'Today', icon: 'sun' },
    { id: 'wardrobe', label: 'Wardrobe', icon: 'shirt' },
    { id: 'history', label: 'History', icon: 'time' },
    { id: 'profile', label: 'Profile', icon: 'person' },
  ];

  const Icon = ({ id, color }) => {
    const c = color;
    const sw = 1.6;
    if (id === 'sun') return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="4"/>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
      </svg>
    );
    if (id === 'shirt') return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 3l-2 2a3 3 0 01-4 0L8 3 3 6l2 5h2v10h10V11h2l2-5z"/>
      </svg>
    );
    if (id === 'time') return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 7v5l3 2"/>
      </svg>
    );
    if (id === 'person') return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4"/>
        <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
      </svg>
    );
    return null;
  };

  if (variant === 'edge') {
    return (
      <div style={{
        position: 'absolute', left: 0, right: 0, bottom: 0,
        background: t.bgDeep,
        borderTop: `1px solid ${t.borderSoft}`,
        paddingBottom: SAFE_BOTTOM,
        zIndex: 30,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', padding: '10px 12px 12px' }}>
          {tabs.map(tab => {
            const isActive = tab.id === active;
            const c = isActive ? t.moss : t.textTer;
            return (
              <div key={tab.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, position: 'relative' }}>
                <Icon id={tab.icon} color={c}/>
                <div style={{
                  fontFamily: FONT_MONO, fontSize: 9, letterSpacing: '0.15em',
                  textTransform: 'uppercase', color: c,
                }}>{tab.label}</div>
                {isActive && (
                  <div style={{
                    position: 'absolute', top: -10, width: 4, height: 4, borderRadius: 2,
                    background: t.moss, boxShadow: `0 0 6px ${t.moss}`,
                  }}/>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Floating pill bar (default)
  return (
    <div style={{
      position: 'absolute', left: 16, right: 16,
      bottom: SAFE_BOTTOM + 6,
      zIndex: 30,
    }}>
      <div style={{
        background: t.bgRaised,
        border: `1px solid ${t.borderSoft}`,
        borderRadius: 28,
        padding: '10px 8px',
        display: 'flex', justifyContent: 'space-around',
        boxShadow: `0 12px 32px rgba(0,0,0,0.35), 0 0 0 1px rgba(212,168,84,0.04)`,
        backdropFilter: 'blur(12px)',
      }}>
        {tabs.map(tab => {
          const isActive = tab.id === active;
          const c = isActive ? t.text : t.textTer;
          return (
            <div key={tab.id} style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              gap: 3, padding: '4px 14px',
              transform: isActive ? 'scale(1.04)' : 'scale(1)',
              transition: 'transform 0.2s',
            }}>
              <Icon id={tab.icon} color={c}/>
              <div style={{
                width: 4, height: 4, borderRadius: 2,
                background: isActive ? t.moss : 'transparent',
                boxShadow: isActive ? `0 0 6px ${t.moss}` : 'none',
                marginTop: 2,
              }}/>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Phone background with grain
function PhoneBg({ t, children, withGrain = true }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: t.bgDeep,
      fontFamily: FONT_BODY,
      color: t.text,
      overflow: 'hidden',
    }}>
      {withGrain && (
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: GRAIN_URL,
          backgroundSize: '220px 220px',
          opacity: 0.55,
          pointerEvents: 'none',
          mixBlendMode: 'overlay',
        }}/>
      )}
      {children}
    </div>
  );
}

Object.assign(window, { SCREEN_W, SCREEN_H, SAFE_TOP, SAFE_BOTTOM, AttreqTabBar, PhoneBg, StatusSpacer });
