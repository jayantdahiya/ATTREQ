
// ─── ATTREQ Design System ───────────────────────────────────────────────────

const THEMES = {
  noir: {
    name: 'Noir',
    bgDeep:      '#0D1210',
    bgSurface:   '#141D19',
    bgRaised:    '#1C2923',
    bgSunk:      '#090D0B',
    accentMoss:  '#3D7255',
    accentOlive: '#7A9962',
    accentGold:  '#D4A854',
    accentClay:  '#C9604A',
    textPrimary: '#F0EDE6',
    textSecondary:'#9B978E',
    textTertiary: '#5C5850',
    borderSubtle: '#1F2B24',
    borderSoft:   'rgba(240,237,230,0.07)',
    mossSoft:     'rgba(61,114,85,0.22)',
    goldSoft:     'rgba(212,168,84,0.18)',
    glowMoss:     'rgba(61,114,85,0.09)',
    glowGold:     'rgba(212,168,84,0.07)',
    navBg:        'rgba(20,29,25,0.92)',
    cardBg:       'rgba(28,41,35,0.80)',
    pillBg:       '#1C2923',
    isDark: true,
  },
  cream: {
    name: 'Cream',
    bgDeep:       '#EEE8DC',
    bgSurface:    '#F5F0E8',
    bgRaised:     '#FFFFFF',
    bgSunk:       '#E5DFD0',
    accentMoss:   '#2F5A40',
    accentOlive:  '#5A7344',
    accentGold:   '#A8842F',
    accentClay:   '#A8492F',
    textPrimary:  '#1C2219',
    textSecondary:'#6A6659',
    textTertiary: '#9A9689',
    borderSubtle: 'rgba(28,34,25,0.10)',
    borderSoft:   'rgba(28,34,25,0.07)',
    mossSoft:     'rgba(47,90,64,0.12)',
    goldSoft:     'rgba(168,132,47,0.16)',
    glowMoss:     'rgba(47,90,64,0.05)',
    glowGold:     'rgba(168,132,47,0.06)',
    navBg:        'rgba(255,255,255,0.92)',
    cardBg:       'rgba(255,255,255,0.85)',
    pillBg:       '#FFFFFF',
    isDark: false,
  },
  slate: {
    name: 'Slate',
    bgDeep:       '#F0F2F5',
    bgSurface:    '#F8F9FB',
    bgRaised:     '#FFFFFF',
    bgSunk:       '#E4E7EC',
    accentMoss:   '#2D6B4F',
    accentOlive:  '#507A55',
    accentGold:   '#B8922A',
    accentClay:   '#B85040',
    textPrimary:  '#18202A',
    textSecondary:'#5A6475',
    textTertiary: '#8A94A5',
    borderSubtle: 'rgba(24,32,42,0.10)',
    borderSoft:   'rgba(24,32,42,0.07)',
    mossSoft:     'rgba(45,107,79,0.12)',
    goldSoft:     'rgba(184,146,42,0.15)',
    glowMoss:     'rgba(45,107,79,0.06)',
    glowGold:     'rgba(184,146,42,0.05)',
    navBg:        'rgba(255,255,255,0.94)',
    cardBg:       'rgba(255,255,255,0.90)',
    pillBg:       '#FFFFFF',
    isDark: false,
  },
};

// ─── Token helpers ────────────────────────────────────────────────────────────
const f = {
  display: `"Cormorant Garamond", Georgia, serif`,
  body: `"DM Sans", system-ui, sans-serif`,
  mono: `"IBM Plex Mono", "Courier New", monospace`,
};

// ─── Shared micro-components ─────────────────────────────────────────────────

function MonoLabel({ children, color, style, size = 9 }) {
  return (
    <span style={{
      fontFamily: f.mono,
      fontSize: size,
      fontWeight: 500,
      letterSpacing: '0.16em',
      textTransform: 'uppercase',
      color: color || 'inherit',
      ...style,
    }}>{children}</span>
  );
}

function Tag({ children, bg, color, border }) {
  return (
    <span style={{
      fontFamily: f.mono, fontSize: 8, letterSpacing: '0.14em',
      textTransform: 'uppercase', fontWeight: 500,
      background: bg || 'transparent',
      color: color || '#888',
      border: `1px solid ${border || 'transparent'}`,
      borderRadius: 100, padding: '3px 8px',
      whiteSpace: 'nowrap',
    }}>{children}</span>
  );
}

function Divider({ color, style }) {
  return <div style={{ height: 1, background: color || 'rgba(255,255,255,0.07)', width: '100%', ...style }} />;
}

// Garment placeholder tile
function GarmentTile({ tone = 'top', label, img, style, className }) {
  const palettes = {
    top:    { a: '#2A3A30', b: '#1E2E24', dot: '#6F8B57' },
    bottom: { a: '#2A2418', b: '#1E1A10', dot: '#8A6F4A' },
    accent: { a: '#3A2A1E', b: '#2A1E14', dot: '#C9604A' },
    shoes:  { a: '#1A1A16', b: '#111110', dot: '#5C5850' },
    outer:  { a: '#2E2A22', b: '#221E16', dot: '#D4A854' },
  };
  const p = palettes[tone] || palettes.top;
  return (
    <div style={{
      borderRadius: 14,
      overflow: 'hidden',
      background: `linear-gradient(135deg, ${p.a}, ${p.b})`,
      position: 'relative',
      ...style,
    }}>
      {img && <img src={img} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} alt="" />}
      {!img && <div style={{ position: 'absolute', top: 10, right: 10, width: 6, height: 6, borderRadius: '50%', background: p.dot, opacity: 0.7 }} />}
      {label && (
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          background: 'linear-gradient(transparent, rgba(0,0,0,0.65))',
          padding: '18px 10px 8px',
        }}>
          <MonoLabel style={{ color: '#F0EDE6' }}>{label}</MonoLabel>
        </div>
      )}
    </div>
  );
}

// Card wrapper
function Card({ children, t, onClick, style, accent, dashed }) {
  return (
    <div onClick={onClick} style={{
      background: t.cardBg,
      border: `1px ${dashed ? 'dashed' : 'solid'} ${t.borderSoft}`,
      borderRadius: 22,
      overflow: 'hidden',
      position: 'relative',
      boxShadow: `0 8px 32px rgba(0,0,0,${t.isDark ? '0.28' : '0.06'})`,
      cursor: onClick ? 'pointer' : 'default',
      ...style,
    }}>
      {accent && (
        <div style={{
          position: 'absolute', top: 0, left: 20, right: 20, height: 2,
          background: accent === 'gold' ? t.accentGold : accent === 'moss' ? t.accentMoss : t.accentClay,
          borderRadius: '0 0 2px 2px',
        }} />
      )}
      {children}
    </div>
  );
}

// Status pill
function Pill({ children, variant, t }) {
  const palettes = {
    gold:  { bg: t.goldSoft, color: t.accentGold, border: 'transparent' },
    moss:  { bg: t.mossSoft, color: t.accentOlive, border: 'transparent' },
    clay:  { bg: 'transparent', color: t.accentClay, border: t.accentClay },
    muted: { bg: 'transparent', color: t.textTertiary, border: t.borderSubtle },
  };
  const p = palettes[variant] || palettes.muted;
  return (
    <span style={{
      background: p.bg, color: p.color, border: `1px solid ${p.border}`,
      borderRadius: 100, padding: '3px 10px',
      fontFamily: f.mono, fontSize: 8, letterSpacing: '0.14em', textTransform: 'uppercase', fontWeight: 500,
    }}>{children}</span>
  );
}

// Icon button circle
function IconBtn({ children, t, onClick, size = 36 }) {
  return (
    <div onClick={onClick} style={{
      width: size, height: size, borderRadius: '50%',
      background: t.bgSurface, border: `1px solid ${t.borderSoft}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer', flexShrink: 0,
    }}>{children}</div>
  );
}

// SVG icons (minimal set, drawn simply)
function Icon({ name, size = 18, color = 'currentColor' }) {
  const icons = {
    sun: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></svg>,
    shirt: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.57a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.57a2 2 0 00-1.34-2.23z"/></svg>,
    albums: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 2H8l-2 5h12l-2-5z"/></svg>,
    person: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>,
    location: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>,
    refresh: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>,
    heart: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>,
    close: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
    check: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>,
    camera: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>,
    images: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><rect x="2" y="5" width="16" height="14" rx="2"/><path d="M22 3H8"/><path d="M2 9l5 5 4-4 4 5"/></svg>,
    search: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
    bell: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>,
    chevron: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>,
    cloud: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/></svg>,
    menu: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
    eye: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>,
    logout: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
    swipeRight: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>,
    swipeLeft: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>,
  };
  return icons[name] || null;
}

// Primary button
function Btn({ label, icon, variant = 'primary', t, onClick, style, full }) {
  const palettes = {
    primary: { bg: t.accentMoss, border: t.accentMoss, color: '#F0EDE6' },
    secondary: { bg: t.bgRaised, border: t.borderSubtle, color: t.textPrimary },
    ghost: { bg: 'transparent', border: 'transparent', color: t.accentGold },
    premium: { bg: t.accentGold, border: t.accentGold, color: '#1A1208' },
    danger: { bg: 'transparent', border: t.accentClay, color: t.accentClay },
  };
  const p = palettes[variant] || palettes.primary;
  return (
    <div onClick={onClick} style={{
      background: p.bg, border: `1px solid ${p.border}`, color: p.color,
      borderRadius: 14, padding: '11px 18px', minHeight: 44,
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
      fontFamily: f.body, fontSize: 14, fontWeight: 600,
      cursor: 'pointer', width: full ? '100%' : undefined,
      ...style,
    }}>
      {icon && <span style={{ display: 'flex' }}>{icon}</span>}
      {label}
    </div>
  );
}

// Input field
function Input({ label, type = 'text', placeholder, t, value, onChange }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <MonoLabel color={t.textTertiary}>{label}</MonoLabel>
      <div style={{
        borderBottom: `1.5px solid ${t.borderSubtle}`,
        padding: '8px 0',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        <input
          type={type}
          placeholder={placeholder || ''}
          defaultValue={value}
          style={{
            background: 'transparent', border: 'none', outline: 'none',
            color: t.textPrimary, fontFamily: f.body, fontSize: 15,
            width: '100%',
          }}
        />
      </div>
    </div>
  );
}

// Toggle switch
function Toggle({ on, t }) {
  return (
    <div style={{
      width: 42, height: 24, borderRadius: 100,
      background: on ? t.accentMoss : t.borderSubtle,
      position: 'relative', transition: 'background 0.2s',
      cursor: 'pointer',
    }}>
      <div style={{
        position: 'absolute', top: 3, left: on ? 21 : 3,
        width: 18, height: 18, borderRadius: '50%',
        background: '#fff', transition: 'left 0.2s',
      }} />
    </div>
  );
}

// ─── Bottom Tab Bar ──────────────────────────────────────────────────────────

function TabBar({ active, onTab, t }) {
  const tabs = [
    { id: 'today',   label: 'Today',   icon: 'sun' },
    { id: 'wardrobe',label: 'Wardrobe',icon: 'shirt' },
    { id: 'history', label: 'History', icon: 'albums' },
    { id: 'profile', label: 'Profile', icon: 'person' },
  ];
  return (
    <div style={{
      position: 'absolute', bottom: 20, left: 12, right: 12,
      background: t.navBg,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderRadius: 26,
      border: `1px solid ${t.borderSoft}`,
      boxShadow: `0 16px 48px rgba(0,0,0,${t.isDark ? '0.45' : '0.12'})`,
      padding: '8px 6px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-around',
      zIndex: 50,
    }}>
      {tabs.map(tab => {
        const isFocused = active === tab.id;
        return (
          <div key={tab.id} onClick={() => onTab(tab.id)} style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
            padding: '4px 10px', borderRadius: 18, cursor: 'pointer',
            background: isFocused ? t.mossSoft : 'transparent',
            transition: 'background 0.2s',
            flex: 1,
          }}>
            <Icon name={tab.icon} size={20} color={isFocused ? t.accentMoss : t.textTertiary} />
            <MonoLabel size={7.5} style={{ color: isFocused ? t.accentMoss : t.textTertiary, letterSpacing: '0.12em' }}>
              {tab.label}
            </MonoLabel>
          </div>
        );
      })}
    </div>
  );
}

// ─── Screen: LOGIN ───────────────────────────────────────────────────────────

function LoginScreen({ t, onNavigate }) {
  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, position: 'relative', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Background gradient */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 380,
        background: `linear-gradient(180deg, ${t.bgSurface} 0%, ${t.bgDeep} 100%)`,
        opacity: 0.7, pointerEvents: 'none',
      }} />
      {/* Subtle texture lines */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        {[0,1,2,3].map(i => (
          <div key={i} style={{
            position: 'absolute', left: `${20 + i * 22}%`, top: 0, bottom: 0, width: 1,
            background: `linear-gradient(180deg, transparent, ${t.borderSoft} 40%, transparent)`,
            opacity: 0.5,
          }} />
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '48px 28px 32px', position: 'relative', zIndex: 1 }}>
        {/* Hero */}
        <div style={{ textAlign: 'center', paddingTop: 24 }}>
          <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 16 }}>est. 2026 — personal styling</MonoLabel>
          <div style={{
            fontFamily: f.display, fontSize: 58, fontWeight: 600,
            letterSpacing: '0.16em', color: t.accentGold,
            lineHeight: 1, marginBottom: 12,
          }}>ATTREQ</div>
          <div style={{
            fontFamily: f.display, fontSize: 20, fontStyle: 'italic',
            color: t.textSecondary, fontWeight: 400,
          }}>Your closet, curated.</div>
        </div>

        {/* Form card */}
        <Card t={t} accent="gold" style={{ padding: '28px 24px' }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: f.display, fontSize: 24, fontWeight: 600, color: t.textPrimary, marginBottom: 4 }}>Welcome back</div>
            <div style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary }}>Sign in to your wardrobe.</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <Input label="Email" type="email" placeholder="you@example.com" t={t} />
            <Input label="Password" type="password" placeholder="••••••••" t={t} />
          </div>
          <div style={{ marginTop: 24 }}>
            <Btn label="Sign in" t={t} full onClick={() => onNavigate('today')} style={{ borderRadius: 16 }} />
          </div>
          <div style={{ marginTop: 14, textAlign: 'center' }}>
            <MonoLabel color={t.textTertiary}>Forgot password</MonoLabel>
          </div>
        </Card>

        {/* Footer */}
        <div style={{ textAlign: 'center' }}>
          <span style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary }}>New here? </span>
          <span onClick={() => onNavigate('register')} style={{ fontFamily: f.body, fontSize: 13, fontWeight: 600, color: t.accentGold, cursor: 'pointer' }}>Create account</span>
        </div>
      </div>
    </div>
  );
}

// ─── Screen: REGISTER ────────────────────────────────────────────────────────

function RegisterScreen({ t, onNavigate }) {
  const steps = ['Account', 'Style', 'Location'];
  const [step, setStep] = React.useState(0);

  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, position: 'relative', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 280,
        background: `linear-gradient(180deg, ${t.bgSurface} 0%, ${t.bgDeep} 100%)`,
        opacity: 0.7,
      }} />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '48px 28px 32px', position: 'relative', zIndex: 1, overflowY: 'auto' }}>
        {/* Back + step */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div onClick={() => step > 0 ? setStep(s => s-1) : onNavigate('login')} style={{ cursor: 'pointer', color: t.textSecondary }}>
            <Icon name="swipeLeft" size={20} color={t.textSecondary} />
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {steps.map((s, i) => (
              <div key={s} style={{
                height: 3, width: i === step ? 24 : 8, borderRadius: 100,
                background: i <= step ? t.accentGold : t.borderSubtle,
                transition: 'all 0.3s',
              }} />
            ))}
          </div>
          <MonoLabel color={t.textTertiary}>{`0${step + 1}/${steps.length}`}</MonoLabel>
        </div>

        {/* Step header */}
        <MonoLabel color={t.accentGold} style={{ display: 'block', marginBottom: 10 }}>Step 0{step+1} — {steps[step]}</MonoLabel>
        <div style={{ fontFamily: f.display, fontSize: 34, fontWeight: 600, color: t.textPrimary, lineHeight: 1.1, marginBottom: 6 }}>
          {step === 0 && <>Make this<br /><span style={{ fontStyle: 'italic', color: t.accentGold }}>your closet.</span></>}
          {step === 1 && <>Define your<br /><span style={{ fontStyle: 'italic', color: t.accentGold }}>aesthetic.</span></>}
          {step === 2 && <>Set your<br /><span style={{ fontStyle: 'italic', color: t.accentGold }}>world.</span></>}
        </div>
        <div style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary, marginBottom: 28 }}>
          {step === 0 && "A few details, then we'll curate every look."}
          {step === 1 && "Tell us how you dress. We'll learn the rest."}
          {step === 2 && "Your city shapes every recommendation."}
        </div>

        {/* Step content */}
        <Card t={t} style={{ padding: '24px 20px' }}>
          {step === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <Input label="Email" type="email" placeholder="you@example.com" t={t} />
              <Input label="Full name" placeholder="Alex Kim" t={t} />
              <Input label="Password" type="password" placeholder="At least 8 characters" t={t} />
              <Input label="Confirm password" type="password" placeholder="••••••••" t={t} />
            </div>
          )}
          {step === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 4 }}>Style keywords</MonoLabel>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {['Minimal', 'Earthy', 'Tailored', 'Layered', 'Casual', 'Formal', 'Streetwear', 'Athleisure'].map(tag => (
                  <div key={tag} style={{
                    padding: '7px 14px', borderRadius: 100,
                    border: `1px solid ${['Minimal','Earthy','Layered'].includes(tag) ? t.accentMoss : t.borderSubtle}`,
                    background: ['Minimal','Earthy','Layered'].includes(tag) ? t.mossSoft : 'transparent',
                    cursor: 'pointer',
                  }}>
                    <span style={{ fontFamily: f.body, fontSize: 13, color: ['Minimal','Earthy','Layered'].includes(tag) ? t.accentOlive : t.textSecondary }}>
                      {tag}
                    </span>
                  </div>
                ))}
              </div>
              <Divider color={t.borderSoft} style={{ margin: '8px 0' }} />
              <Input label="Occasions (optional)" placeholder="Work, weekend, travel…" t={t} />
            </div>
          )}
          {step === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div style={{
                borderRadius: 16, overflow: 'hidden', height: 120,
                background: `linear-gradient(135deg, ${t.bgRaised}, ${t.glowMoss})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                border: `1px dashed ${t.borderSubtle}`,
              }}>
                <Icon name="location" size={22} color={t.accentMoss} />
                <div>
                  <div style={{ fontFamily: f.body, fontSize: 14, color: t.textPrimary, fontWeight: 500 }}>Use device location</div>
                  <div style={{ fontFamily: f.body, fontSize: 11, color: t.textSecondary }}>For weather-aware suggestions</div>
                </div>
              </div>
              <Input label="Or enter your city" placeholder="New York, London, Tokyo…" t={t} />
            </div>
          )}
        </Card>

        <div style={{ marginTop: 20 }}>
          <Btn
            label={step < 2 ? 'Continue' : 'Create account'}
            t={t}
            full
            variant={step < 2 ? 'primary' : 'premium'}
            onClick={() => step < 2 ? setStep(s => s+1) : onNavigate('today')}
            style={{ borderRadius: 16 }}
          />
        </div>

        <div style={{ textAlign: 'center', marginTop: 14 }}>
          <span style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary }}>Already have an account? </span>
          <span onClick={() => onNavigate('login')} style={{ fontFamily: f.body, fontSize: 13, fontWeight: 600, color: t.accentGold, cursor: 'pointer' }}>Sign in</span>
        </div>
      </div>
    </div>
  );
}

// ─── Screen: DASHBOARD (Today) ───────────────────────────────────────────────

function SwipeableCard({ t, suggestion, index }) {
  const [offset, setOffset] = React.useState(0);
  const [dragging, setDragging] = React.useState(false);
  const [decision, setDecision] = React.useState(null); // 'wear' | 'skip' | null
  const startX = React.useRef(null);

  const threshold = 80;

  const handleMouseDown = (e) => {
    startX.current = e.clientX;
    setDragging(true);
    setDecision(null);
  };
  const handleMouseMove = (e) => {
    if (!dragging || startX.current === null) return;
    const dx = e.clientX - startX.current;
    setOffset(dx);
    if (dx > threshold / 2) setDecision('wear');
    else if (dx < -threshold / 2) setDecision('skip');
    else setDecision(null);
  };
  const handleMouseUp = () => {
    if (!dragging) return;
    setDragging(false);
    if (offset > threshold) {
      setDecision('wear');
    } else if (offset < -threshold) {
      setDecision('skip');
    } else {
      setDecision(null);
    }
    setOffset(0);
    startX.current = null;
  };

  const toneA = ['top', 'bottom', 'accent'][index % 3];
  const toneB = ['bottom', 'outer', 'top'][index % 3];
  const lookNames = ['The Morning Walk', 'Studio Session', 'Golden Hour', 'Weekend Edit', 'Quiet Monday'];
  const lookName = lookNames[index % lookNames.length];
  const score = 78 + index * 5;
  const temps = ['14°C — Overcast', '22°C — Sunny', '9°C — Crisp', '18°C — Partly cloudy'];
  const temp = temps[index % temps.length];
  const occasions = ['Casual', 'Smart Casual', 'Work', 'Weekend'];
  const occasion = occasions[index % occasions.length];

  return (
    <div style={{ position: 'relative', userSelect: 'none' }}>
      {/* Swipe hint indicators */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 22, zIndex: 0,
        background: decision === 'wear'
          ? `linear-gradient(90deg, ${t.mossSoft} 0%, transparent 60%)`
          : decision === 'skip'
          ? `linear-gradient(270deg, rgba(201,96,74,0.18) 0%, transparent 60%)`
          : 'transparent',
        transition: dragging ? 'none' : 'background 0.3s',
        pointerEvents: 'none',
        display: 'flex', alignItems: 'center', justifyContent: decision === 'wear' ? 'flex-start' : 'flex-end', padding: '0 20px',
      }}>
        {decision === 'wear' && <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Icon name="check" size={18} color={t.accentMoss} />
          <MonoLabel color={t.accentMoss}>Wear this</MonoLabel>
        </div>}
        {decision === 'skip' && <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <MonoLabel color={t.accentClay}>Skip</MonoLabel>
          <Icon name="close" size={18} color={t.accentClay} />
        </div>}
      </div>

      <Card t={t} style={{
        padding: '16px',
        transform: `translateX(${offset}px) rotate(${offset * 0.03}deg)`,
        transition: dragging ? 'none' : 'transform 0.35s cubic-bezier(.34,1.56,.64,1)',
        cursor: dragging ? 'grabbing' : 'grab',
        position: 'relative', zIndex: 1,
        boxShadow: `0 ${8 + Math.abs(offset) * 0.1}px ${32 + Math.abs(offset) * 0.2}px rgba(0,0,0,${t.isDark ? '0.3' : '0.08'})`,
      }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Card header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <MonoLabel color={t.accentGold}>Look {String(index + 1).padStart(2, '0')}</MonoLabel>
            <div style={{ fontFamily: f.display, fontSize: 22, fontStyle: 'italic', fontWeight: 600, color: t.textPrimary, marginTop: 2, lineHeight: 1.1 }}>
              {lookName}
            </div>
          </div>
          <Pill variant="muted" t={t}>{score}% match</Pill>
        </div>

        {/* Garment tiles */}
        <div style={{ display: 'flex', gap: 8, height: 200 }}>
          <GarmentTile tone={toneA} label="Top" style={{ flex: 1.6, height: '100%' }} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <GarmentTile tone={toneB} label="Bottom" style={{ flex: 1.6, minHeight: 0 }} />
            <GarmentTile tone="accent" label="Accent" style={{ flex: 1, minHeight: 0 }} />
          </div>
        </div>

        {/* Context strip */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12, marginBottom: 14 }}>
          <MonoLabel color={t.textTertiary}>{temp}</MonoLabel>
          <MonoLabel color={t.accentOlive}>— {occasion}</MonoLabel>
        </div>

        {/* Swipe hint */}
        <div style={{
          borderTop: `1px solid ${t.borderSoft}`, paddingTop: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: t.textTertiary }}>
              <Icon name="swipeLeft" size={14} color={t.textTertiary} />
              <MonoLabel color={t.textTertiary}>Skip</MonoLabel>
            </div>
            <div style={{ width: 1, height: 12, background: t.borderSubtle }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <MonoLabel color={t.accentMoss}>Wear</MonoLabel>
              <Icon name="swipeRight" size={14} color={t.accentMoss} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{
              width: 34, height: 34, borderRadius: '50%', border: `1px solid ${t.borderSoft}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              background: t.bgRaised,
            }}>
              <Icon name="heart" size={15} color={t.accentGold} />
            </div>
            <div style={{
              width: 34, height: 34, borderRadius: '50%', border: `1px solid ${t.borderSubtle}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              background: t.bgRaised,
            }}>
              <Icon name="close" size={15} color={t.textSecondary} />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function DashboardScreen({ t }) {
  const date = new Intl.DateTimeFormat('en', { weekday: 'long', month: '2-digit', day: '2-digit' }).format(new Date());
  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '52px 22px 110px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 22 }}>
          <div>
            <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 6 }}>{date}</MonoLabel>
            <div style={{ fontFamily: f.display, fontSize: 32, fontWeight: 600, color: t.textPrimary, lineHeight: 1.1 }}>
              Good morning,<br />
              <span style={{ fontStyle: 'italic', color: t.accentGold }}>Alex.</span>
            </div>
          </div>
          <IconBtn t={t}>
            <Icon name="menu" size={16} color={t.textSecondary} />
          </IconBtn>
        </div>

        {/* Weather strip */}
        <div style={{
          background: t.cardBg,
          border: `1px solid ${t.borderSoft}`,
          borderRadius: 18,
          padding: '14px 16px',
          display: 'flex', alignItems: 'center', gap: 14,
          marginBottom: 24,
          backdropFilter: 'blur(12px)',
        }}>
          <div style={{
            width: 42, height: 42, borderRadius: '50%',
            background: t.glowGold, border: `1px solid ${t.goldSoft}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Icon name="sun" size={20} color={t.accentGold} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: f.body, fontSize: 14, fontWeight: 500, color: t.textPrimary }}>New York City</div>
            <div style={{ fontFamily: f.body, fontSize: 12, color: t.textSecondary }}>Partly cloudy — 18°C</div>
          </div>
          <div>
            <div style={{ fontFamily: f.display, fontSize: 26, fontWeight: 600, color: t.accentOlive }}>18°</div>
          </div>
        </div>

        {/* Section title */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ fontFamily: f.display, fontSize: 22, fontStyle: 'italic', fontWeight: 600, color: t.textPrimary }}>
            Today's looks
          </div>
          <MonoLabel color={t.textTertiary}>3 looks</MonoLabel>
        </div>

        {/* Quick actions */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <Btn icon={<Icon name="refresh" size={14} color={t.textPrimary} />} label="Refresh" t={t} variant="secondary" style={{ fontSize: 12, padding: '8px 14px', borderRadius: 12 }} />
          <Btn icon={<Icon name="location" size={14} color={t.accentGold} />} label="Update location" t={t} variant="ghost" style={{ fontSize: 12, padding: '8px 14px', borderRadius: 12 }} />
        </div>

        {/* Swipeable outfit cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[0, 1, 2].map(i => (
            <SwipeableCard key={i} t={t} suggestion={{}} index={i} />
          ))}
        </div>

        {/* Footer hint card */}
        <Card t={t} style={{ padding: '14px 16px', marginTop: 14 }}>
          <MonoLabel color={t.accentGold} style={{ display: 'block', marginBottom: 6 }}>Motion note</MonoLabel>
          <div style={{ fontFamily: f.body, fontSize: 12, color: t.textSecondary }}>
            Drag cards left to skip, right to wear. Pull down to refresh with latest weather.
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── Screen: WARDROBE ────────────────────────────────────────────────────────

function WardrobeScreen({ t }) {
  const [activeFilter, setActiveFilter] = React.useState('All');
  const categories = ['All', 'Tops', 'Bottoms', 'Outer', 'Accents', 'Shoes'];
  const tones = ['top', 'bottom', 'outer', 'accent', 'top', 'shoes', 'bottom', 'outer', 'accent', 'top'];
  const itemLabels = ['Merino Crewneck', 'Linen Trousers', 'Wool Overcoat', 'Canvas Tote', 'Oxford Shirt', 'Chino Shorts', 'Field Jacket', 'Silk Scarf', 'Derby Shoes', 'Cashmere Vest'];
  const colors = ['Ecru', 'Stone', 'Camel', 'Forest', 'White', 'Khaki', 'Olive', 'Rust', 'Tan', 'Cream'];

  const col1 = [0, 2, 4, 6, 8];
  const col2 = [1, 3, 5, 7, 9];
  const heights = [200, 240, 170, 215, 190, 230, 200, 180, 220, 250];

  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '52px 22px 110px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 4 }}>
          <div>
            <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 6 }}>Closet</MonoLabel>
            <div style={{ fontFamily: f.display, fontSize: 32, fontWeight: 600, color: t.textPrimary }}>Wardrobe</div>
          </div>
          <IconBtn t={t}>
            <Icon name="search" size={16} color={t.textSecondary} />
          </IconBtn>
        </div>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center', marginBottom: 18 }}>
          <span style={{ fontFamily: f.body, fontSize: 13, color: t.accentGold, fontWeight: 500 }}>10 pieces</span>
          <span style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary }}> — last added 2d ago</span>
        </div>

        {/* Category filter chips */}
        <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4, marginBottom: 18, marginLeft: -22, paddingLeft: 22, marginRight: -22, paddingRight: 22 }}>
          {categories.map((cat, i) => {
            const active = activeFilter === cat;
            return (
              <div key={cat} onClick={() => setActiveFilter(cat)} style={{
                padding: '7px 16px', borderRadius: 100, cursor: 'pointer', whiteSpace: 'nowrap',
                background: active ? t.textPrimary : 'transparent',
                border: `1px solid ${active ? t.textPrimary : t.borderSubtle}`,
                flexShrink: 0,
              }}>
                <MonoLabel size={8} style={{ color: active ? t.bgDeep : t.textSecondary }}>{cat}</MonoLabel>
              </div>
            );
          })}
        </div>

        {/* Upload actions */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
          <Card t={t} dashed style={{ flex: 1, padding: '16px 14px', cursor: 'pointer', background: t.glowMoss }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: t.accentMoss, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
              <Icon name="camera" size={15} color="#F0EDE6" />
            </div>
            <div style={{ fontFamily: f.display, fontSize: 16, fontWeight: 600, color: t.textPrimary }}>Camera</div>
            <div style={{ fontFamily: f.body, fontSize: 11, color: t.textSecondary, marginTop: 2 }}>Capture a piece</div>
          </Card>
          <Card t={t} dashed style={{ flex: 1, padding: '16px 14px', cursor: 'pointer' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: t.bgRaised, border: `1px solid ${t.borderSoft}`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
              <Icon name="images" size={15} color={t.accentGold} />
            </div>
            <div style={{ fontFamily: f.display, fontSize: 16, fontWeight: 600, color: t.textPrimary }}>Library</div>
            <div style={{ fontFamily: f.body, fontSize: 11, color: t.textSecondary, marginTop: 2 }}>From photos</div>
          </Card>
        </div>

        {/* Masonry grid */}
        <div style={{ display: 'flex', gap: 10 }}>
          {[col1, col2].map((col, colIdx) => (
            <div key={colIdx} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {col.map(idx => (
                <div key={idx}>
                  <GarmentTile
                    tone={tones[idx]}
                    label={itemLabels[idx]}
                    style={{ height: heights[idx], borderRadius: 18 }}
                  />
                  <div style={{ padding: '8px 2px 0' }}>
                    <div style={{ fontFamily: f.display, fontSize: 14, fontStyle: 'italic', fontWeight: 600, color: t.textPrimary }}>{itemLabels[idx]}</div>
                    <MonoLabel color={t.textTertiary}>{colors[idx]}</MonoLabel>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Screen: HISTORY ─────────────────────────────────────────────────────────

function HistoryScreen({ t }) {
  const days = [
    {
      date: 'Thursday, 05/01',
      key: '2026-05-01',
      outfits: [
        { name: 'The Morning Walk', status: 'Worn', variant: 'moss', pieces: 3 },
        { name: 'Studio Session', status: 'Loved', variant: 'gold', pieces: 3 },
      ],
    },
    {
      date: 'Wednesday, 04/30',
      key: '2026-04-30',
      outfits: [
        { name: 'Golden Hour', status: 'Worn', variant: 'moss', pieces: 3 },
      ],
    },
    {
      date: 'Tuesday, 04/29',
      key: '2026-04-29',
      outfits: [
        { name: 'Weekend Edit', status: 'Skipped', variant: 'clay', pieces: 3 },
        { name: 'Quiet Monday', status: 'Loved', variant: 'gold', pieces: 3 },
      ],
    },
  ];

  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '52px 22px 110px' }}>
        {/* Header */}
        <div style={{ marginBottom: 22 }}>
          <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 6 }}>Diary</MonoLabel>
          <div style={{ fontFamily: f.display, fontSize: 32, fontWeight: 600, color: t.textPrimary }}>History</div>
          <div style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary, marginTop: 4 }}>5 looks tracked</div>
        </div>

        {/* Timeline groups */}
        {days.map((day) => (
          <div key={day.key} style={{ marginBottom: 28 }}>
            {/* Day header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ fontFamily: f.display, fontSize: 18, fontStyle: 'italic', fontWeight: 600, color: t.textPrimary, whiteSpace: 'nowrap' }}>
                {day.date}
              </div>
              <Divider color={t.borderSoft} />
              <MonoLabel color={t.textTertiary} style={{ whiteSpace: 'nowrap' }}>{day.key}</MonoLabel>
            </div>

            {/* Outfit cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {day.outfits.map((outfit, i) => (
                <Card key={i} t={t} style={{ padding: '12px 14px' }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    {/* Mini garment tiles */}
                    <div style={{ display: 'flex', gap: 4 }}>
                      {['top', 'bottom', 'accent'].map(tone => (
                        <GarmentTile key={tone} tone={tone} style={{ width: 38, height: 52, borderRadius: 10 }} />
                      ))}
                    </div>
                    {/* Info */}
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 6 }}>
                      <div>
                        <div style={{ fontFamily: f.display, fontSize: 15, fontStyle: 'italic', fontWeight: 600, color: t.textPrimary, lineHeight: 1.2 }}>
                          {outfit.name}
                        </div>
                        <MonoLabel color={t.textTertiary} style={{ marginTop: 2, display: 'block' }}>{outfit.pieces} pieces</MonoLabel>
                      </div>
                      <Pill variant={outfit.variant} t={t}>{outfit.status}</Pill>
                    </div>
                    {/* Expand chevron */}
                    <Icon name="chevron" size={16} color={t.textTertiary} />
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Screen: PROFILE ─────────────────────────────────────────────────────────

function ProfileScreen({ t, onNavigate }) {
  const [reminders, setReminders] = React.useState(true);

  const stats = [
    { label: 'Pieces', value: '10' },
    { label: 'Worn', value: '14' },
    { label: 'Streak', value: '3d', gold: true },
  ];

  const prefs = [
    { icon: 'location', label: 'New York City', sub: '40.7128 — 74.0060' },
    { icon: 'bell', label: 'Daily reminder', sub: '8:00 AM — weekdays', toggle: true },
    { icon: 'shirt', label: 'Style preferences', sub: 'Minimal · Earthy · Layered', action: 'Edit' },
    { icon: 'eye', label: 'Appearance', sub: 'Dark mode enabled', action: 'Edit' },
  ];

  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '52px 22px 110px' }}>
        {/* Header */}
        <div style={{ marginBottom: 22 }}>
          <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 6 }}>You</MonoLabel>
          <div style={{ fontFamily: f.display, fontSize: 32, fontWeight: 600, color: t.textPrimary }}>Profile</div>
        </div>

        {/* Profile card */}
        <Card t={t} accent="gold" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 18 }}>
            {/* Avatar */}
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              background: t.accentGold, display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <span style={{ fontFamily: f.display, fontSize: 22, fontStyle: 'italic', fontWeight: 600, color: '#1A1208' }}>AK</span>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: f.display, fontSize: 20, fontWeight: 600, color: t.textPrimary }}>Alex Kim</div>
              <div style={{ fontFamily: f.body, fontSize: 12, color: t.textSecondary, marginTop: 2 }}>alex@example.com</div>
            </div>
            <IconBtn t={t} size={32}>
              <Icon name="chevron" size={14} color={t.textTertiary} />
            </IconBtn>
          </div>
          <Divider color={t.borderSoft} />
          <div style={{ display: 'flex', gap: 28, paddingTop: 16 }}>
            {stats.map(s => (
              <div key={s.label}>
                <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 4 }}>{s.label}</MonoLabel>
                <div style={{
                  fontFamily: f.display, fontSize: 22, fontWeight: 600,
                  fontStyle: s.gold ? 'italic' : 'normal',
                  color: s.gold ? t.accentGold : t.textPrimary,
                }}>{s.value}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Preferences */}
        <div style={{ marginTop: 28 }}>
          <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 12 }}>Preferences</MonoLabel>
          <Card t={t} style={{ padding: 0, overflow: 'hidden' }}>
            {prefs.map((pref, i) => (
              <div key={pref.label}>
                {i > 0 && <Divider color={t.borderSoft} />}
                <div style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
                  <div style={{ width: 32, height: 32, borderRadius: '50%', background: t.bgRaised, border: `1px solid ${t.borderSoft}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon name={pref.icon} size={15} color={t.textSecondary} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: f.body, fontSize: 13, fontWeight: 500, color: t.textPrimary }}>{pref.label}</div>
                    <MonoLabel color={t.textTertiary} style={{ display: 'block', marginTop: 2 }}>{pref.sub}</MonoLabel>
                  </div>
                  {pref.toggle && <Toggle on={reminders} t={t} />}
                  {pref.action && <MonoLabel color={t.accentGold} style={{ cursor: 'pointer' }}>{pref.action}</MonoLabel>}
                  {!pref.toggle && !pref.action && <Icon name="chevron" size={14} color={t.textTertiary} />}
                </div>
              </div>
            ))}
          </Card>
        </div>

        {/* Sign out */}
        <div style={{ marginTop: 28, textAlign: 'center' }}>
          <div onClick={() => onNavigate('login')} style={{ display: 'inline-flex', alignItems: 'center', gap: 7, cursor: 'pointer' }}>
            <Icon name="logout" size={14} color={t.accentClay} />
            <MonoLabel color={t.accentClay}>Sign out</MonoLabel>
          </div>
        </div>
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <MonoLabel color={t.textTertiary} style={{ opacity: 0.5 }}>v 1.4.2 — ATTREQ</MonoLabel>
        </div>
      </div>
    </div>
  );
}

// ─── Screen: LOCATION PERMISSION (onboarding) ────────────────────────────────

function LocationPermScreen({ t, onAllow }) {
  return (
    <div style={{ width: '100%', height: '100%', background: t.bgDeep, position: 'relative', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', top: '20%', left: '50%', transform: 'translate(-50%,-50%)', width: 260, height: 260, borderRadius: '50%', background: t.glowMoss, filter: 'blur(60px)' }} />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '60px 28px 36px', position: 'relative', zIndex: 1 }}>
        <div>
          <MonoLabel color={t.textTertiary} style={{ display: 'block', marginBottom: 0 }}>Step 02</MonoLabel>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          {/* Concentric circles */}
          <div style={{ position: 'relative', width: 160, height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 36 }}>
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: `1px solid ${t.borderSoft}`, background: t.glowMoss }} />
            <div style={{ position: 'absolute', inset: 24, borderRadius: '50%', border: `1px dashed ${t.mossSoft}` }} />
            <div style={{ width: 60, height: 60, borderRadius: '50%', background: t.accentMoss, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 32px ${t.mossSoft}` }}>
              <Icon name="location" size={26} color="#F0EDE6" />
            </div>
          </div>
          <div style={{ fontFamily: f.display, fontSize: 32, fontWeight: 600, color: t.textPrimary, lineHeight: 1.15, marginBottom: 12 }}>
            The weather decides<br />
            <span style={{ fontStyle: 'italic', color: t.accentGold }}>before you do.</span>
          </div>
          <div style={{ fontFamily: f.body, fontSize: 13, color: t.textSecondary, maxWidth: 260, lineHeight: 1.5 }}>
            Share your location and we'll pair tomorrow's looks to tomorrow's sky.
          </div>
        </div>
        <div>
          <Btn icon={<Icon name="location" size={15} color="#1A1208" />} label="Allow location access" t={t} variant="premium" full onClick={onAllow} style={{ borderRadius: 16 }} />
          <div style={{ textAlign: 'center', marginTop: 14 }}>
            <MonoLabel color={t.textTertiary}>Maybe later</MonoLabel>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main App shell ──────────────────────────────────────────────────────────

function ATTREQApp({ theme }) {
  const t = THEMES[theme] || THEMES.noir;
  const [screen, setScreen] = React.useState('today');

  const renderScreen = () => {
    switch (screen) {
      case 'login':     return <LoginScreen t={t} onNavigate={setScreen} />;
      case 'register':  return <RegisterScreen t={t} onNavigate={setScreen} />;
      case 'location':  return <LocationPermScreen t={t} onAllow={() => setScreen('today')} />;
      case 'today':     return <DashboardScreen t={t} />;
      case 'wardrobe':  return <WardrobeScreen t={t} />;
      case 'history':   return <HistoryScreen t={t} />;
      case 'profile':   return <ProfileScreen t={t} onNavigate={setScreen} />;
      default:          return <DashboardScreen t={t} />;
    }
  };

  const showTabs = ['today', 'wardrobe', 'history', 'profile'].includes(screen);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', background: t.bgDeep }}>
      {renderScreen()}
      {showTabs && <TabBar active={screen} onTab={setScreen} t={t} />}
    </div>
  );
}

// Export to window
Object.assign(window, {
  THEMES,
  LoginScreen,
  RegisterScreen,
  LocationPermScreen,
  DashboardScreen,
  WardrobeScreen,
  HistoryScreen,
  ProfileScreen,
  TabBar,
});
