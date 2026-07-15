// ATTREQ Design System — tokens, theme context, icons, micro-components

// ─── Light tokens ─────────────────────────────────────────────────────────────
const ATTREQ_C = {
  bg: '#F5F2EE', surface: '#FFFFFF', deep: '#1C1917',
  text: '#1C1917', t2: '#78716C', t3: '#A8A29E',
  accent: '#9B7B5A', accentSoft: 'rgba(155,123,90,0.10)',
  border: 'rgba(28,25,23,0.08)', borderSoft: 'rgba(28,25,23,0.05)',
  clay: '#BF5C45', claySoft: 'rgba(191,92,69,0.10)',
  moss: '#5A8A6A', mossSoft: 'rgba(90,138,106,0.12)',
}

// ─── Dark tokens ──────────────────────────────────────────────────────────────
const ATTREQ_DARK_C = {
  bg: '#181512', surface: '#231F1B', deep: '#EDE9E3',
  text: '#EDE9E3', t2: '#9A9088', t3: '#6E6862',
  accent: '#BA9272', accentSoft: 'rgba(186,146,114,0.13)',
  border: 'rgba(237,233,227,0.08)', borderSoft: 'rgba(237,233,227,0.05)',
  clay: '#D4705A', claySoft: 'rgba(212,112,90,0.12)',
  moss: '#72AA86', mossSoft: 'rgba(114,170,134,0.14)',
}

// ─── Theme context + hook ─────────────────────────────────────────────────────
const ATTREQThemeCtx = React.createContext(null)

function useATTREQTheme() {
  const C = React.useContext(ATTREQThemeCtx) || ATTREQ_C
  const isDark = C.bg === ATTREQ_DARK_C.bg
  const cardStyle = {
    background: C.surface, borderRadius: 20, border: `1px solid ${C.border}`,
    boxShadow: isDark
      ? '0 2px 12px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.04)'
      : '0 2px 8px rgba(0,0,0,0.04), 0 0 1px rgba(0,0,0,0.04)',
  }
  const garmentGrads = isDark ? {
    top:    'linear-gradient(155deg,#3C3630,#302A24)',
    bottom: 'linear-gradient(155deg,#343030,#28242A)',
    outer:  'linear-gradient(155deg,#423A2C,#362E22)',
    accent: 'linear-gradient(155deg,#403C36,#343028)',
    shoes:  'linear-gradient(155deg,#3A3632,#2E2A26)',
  } : {
    top:    'linear-gradient(155deg,#EDE7DF,#DDD6CC)',
    bottom: 'linear-gradient(155deg,#DAD4CC,#CAC3BA)',
    outer:  'linear-gradient(155deg,#E3DACE,#D5CCBF)',
    accent: 'linear-gradient(155deg,#F0EBE3,#E5DED5)',
    shoes:  'linear-gradient(155deg,#DFD9D2,#D3CCC5)',
  }
  return { C, isDark, cardStyle, garmentGrads }
}

// ─── Fonts ────────────────────────────────────────────────────────────────────
const ATTREQ_F = {
  display: "'Cormorant Garamond', Georgia, serif",
  body:    "'DM Sans', system-ui, sans-serif",
  mono:    "'IBM Plex Mono', 'Courier New', monospace",
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const IconSun = ({ size=20, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <circle cx="12" cy="12" r="4"/>
    <line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/>
    <line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/>
    <line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/>
    <line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/>
  </svg>
)
const IconShirt = ({ size=20, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z"/>
  </svg>
)
const IconBook = ({ size=20, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
)
const IconPerson = ({ size=20, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconCamera = ({ size=16, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>
  </svg>
)
const IconImage = ({ size=16, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>
  </svg>
)
const IconLocation = ({ size=16, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
  </svg>
)
const IconSearch = ({ size=15, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
  </svg>
)
const IconBell = ({ size=15, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
)
const IconChevron = ({ size=13, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round">
    <path d="m9 18 6-6-6-6"/>
  </svg>
)
const IconSparkles = ({ size=15, color='#A8A29E' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
  </svg>
)
const IconBack = ({ size=14, color='#78716C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round">
    <path d="m15 18-6-6 6-6"/>
  </svg>
)
const IconCheck = ({ size=14, color='currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round">
    <path d="M20 6 9 17l-5-5"/>
  </svg>
)
const IconHeart = ({ size=14, color='#9B7B5A' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
  </svg>
)
const IconMenu = ({ size=15, color='#78716C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
    <path d="M4 6h16M4 12h16M4 18h16"/>
  </svg>
)
const IconX = ({ size=13, color='#78716C' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round">
    <path d="M18 6 6 18M6 6l12 12"/>
  </svg>
)

// ─── Shared components ────────────────────────────────────────────────────────

function ATTREQStatusBar() {
  const { C } = useATTREQTheme()
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'13px 24px 6px', fontFamily:ATTREQ_F.body, fontSize:12, fontWeight:600, color:C.text, letterSpacing:'-0.2px' }}>
      <span>9:41</span>
      <div style={{ display:'flex', gap:5, alignItems:'center' }}>
        <svg width="17" height="11" viewBox="0 0 17 11">
          <rect x="0"    y="6" width="3" height="5"  rx="0.7" fill={C.text} opacity="0.3"/>
          <rect x="4.5"  y="4" width="3" height="7"  rx="0.7" fill={C.text} opacity="0.55"/>
          <rect x="9"    y="2" width="3" height="9"  rx="0.7" fill={C.text} opacity="0.8"/>
          <rect x="13.5" y="0" width="3" height="11" rx="0.7" fill={C.text}/>
        </svg>
        <svg width="15" height="11" viewBox="0 0 15 11">
          <circle cx="7.5" cy="9.5" r="1.25" fill={C.text}/>
          <path d="M4 6.5C5.1 5.2 6.2 4.5 7.5 4.5s2.4.7 3.5 2" stroke={C.text} strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.6"/>
          <path d="M1.5 3C3.3 1.1 5.3 0 7.5 0s4.2 1.1 6 3" stroke={C.text} strokeWidth="1.2" strokeLinecap="round" fill="none" opacity="0.3"/>
        </svg>
        <svg width="25" height="11" viewBox="0 0 25 11">
          <rect x="0.5" y="0.5" width="21" height="10" rx="3" stroke={C.text} strokeOpacity="0.3" fill="none"/>
          <rect x="2" y="2" width="16.5" height="7" rx="1.5" fill={C.text}/>
          <path d="M22.5 3.5v4a2 2 0 0 0 0-4z" fill={C.text} fillOpacity="0.4"/>
        </svg>
      </div>
    </div>
  )
}

function ATTREQTabBar({ active=0 }) {
  const { C, isDark } = useATTREQTheme()
  const tabs = [
    { label:'TODAY',   Icon:IconSun    },
    { label:'WARDROBE',Icon:IconShirt  },
    { label:'HISTORY', Icon:IconBook   },
    { label:'PROFILE', Icon:IconPerson },
  ]
  const tabBg = isDark ? 'rgba(24,21,18,0.96)' : 'rgba(245,242,238,0.95)'
  const innerGlow = isDark
    ? 'inset 0 1px 0 rgba(255,255,255,0.06)'
    : 'inset 0 1px 0 rgba(255,255,255,0.7)'
  return (
    <div style={{ position:'absolute', bottom:20, left:16, right:16, background:tabBg, backdropFilter:'blur(20px)', borderRadius:22, border:`1px solid ${C.border}`, display:'flex', padding:'6px 4px', boxShadow:`0 8px 32px rgba(0,0,0,${isDark?'0.3':'0.08'}), ${innerGlow}` }}>
      {tabs.map(({ label, Icon }, i) => {
        const on = i === active
        return (
          <div key={i} style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', gap:2, padding:'5px 4px', borderRadius:16, background: on ? (isDark ? 'rgba(237,233,227,0.08)' : 'rgba(28,25,23,0.07)') : 'transparent' }}>
            <Icon size={19} color={on ? C.text : C.t3}/>
            <span style={{ fontFamily:ATTREQ_F.mono, fontSize:7, letterSpacing:'0.7px', color: on ? C.text : C.t3 }}>{label}</span>
          </div>
        )
      })}
    </div>
  )
}

function ATTREQScreen({ children, style }) {
  const { C } = useATTREQTheme()
  return (
    <div style={{ width:390, height:844, position:'relative', overflow:'hidden', background:C.bg, fontFamily:ATTREQ_F.body, ...style }}>
      {children}
    </div>
  )
}

function ATTREQML({ children, color, style }) {
  const { C } = useATTREQTheme()
  return (
    <span style={{ fontFamily:ATTREQ_F.mono, fontSize:9.5, letterSpacing:'1.6px', textTransform:'uppercase', color:color||C.t3, lineHeight:1.4, ...style }}>
      {children}
    </span>
  )
}

function ATTREQBody({ children, color, style }) {
  const { C } = useATTREQTheme()
  return (
    <p style={{ fontFamily:ATTREQ_F.body, fontSize:14, lineHeight:1.5, color:color||C.t2, margin:0, ...style }}>
      {children}
    </p>
  )
}

function ATTREQInput({ label, value }) {
  const { C } = useATTREQTheme()
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:5 }}>
      <ATTREQML>{label}</ATTREQML>
      <div style={{ borderBottom:`1px solid ${C.border}`, padding:'6px 0 8px', fontFamily:ATTREQ_F.body, fontSize:14.5, color: value && value.startsWith('•') ? C.t2 : C.text }}>{value}</div>
    </div>
  )
}

function ATTREQCard({ children, style }) {
  const { cardStyle } = useATTREQTheme()
  return <div style={{ ...cardStyle, ...style }}>{children}</div>
}

function ATTREQChip({ children, selected }) {
  const { C } = useATTREQTheme()
  return (
    <div style={{ display:'inline-flex', alignItems:'center', padding:'6px 14px', borderRadius:100, background: selected ? C.text : 'transparent', border:`1px solid ${selected ? C.text : C.border}`, fontFamily:ATTREQ_F.body, fontSize:13, fontWeight:500, color: selected ? C.bg : C.t2, cursor:'pointer', userSelect:'none' }}>
      {children}
    </div>
  )
}

function ATTREQPill({ children, variant='muted' }) {
  const { C } = useATTREQTheme()
  const map = {
    muted: { bg:`rgba(128,120,112,0.10)`, color:C.t2 },
    gold:  { bg:C.accentSoft, color:C.accent },
    moss:  { bg:C.mossSoft,   color:C.moss   },
    clay:  { bg:C.claySoft,   color:C.clay   },
  }
  const v = map[variant] || map.muted
  return (
    <span style={{ fontFamily:ATTREQ_F.mono, fontSize:8.5, letterSpacing:'0.9px', textTransform:'uppercase', padding:'3px 9px', borderRadius:100, background:v.bg, color:v.color, whiteSpace:'nowrap' }}>
      {children}
    </span>
  )
}

function ATTREQGarment({ tone='top', style, label }) {
  const { C, garmentGrads } = useATTREQTheme()
  return (
    <div style={{ background:garmentGrads[tone]||garmentGrads.top, borderRadius:14, position:'relative', overflow:'hidden', ...style }}>
      {label && <div style={{ position:'absolute', bottom:7, left:8, fontFamily:ATTREQ_F.mono, fontSize:7.5, letterSpacing:'0.8px', textTransform:'uppercase', color:C.t3 }}>{label}</div>}
    </div>
  )
}

function ATTREQBtn({ children, style }) {
  const { C } = useATTREQTheme()
  return (
    <button style={{ background:C.text, color:C.bg, fontFamily:ATTREQ_F.body, fontWeight:500, fontSize:14, border:'none', borderRadius:100, padding:'13px 24px', cursor:'pointer', width:'100%', letterSpacing:'0.2px', display:'flex', alignItems:'center', justifyContent:'center', gap:6, ...style }}>
      {children}
    </button>
  )
}

Object.assign(window, {
  ATTREQ_C, ATTREQ_DARK_C, ATTREQ_F,
  ATTREQThemeCtx, useATTREQTheme,
  ATTREQStatusBar, ATTREQTabBar, ATTREQScreen,
  ATTREQML, ATTREQBody, ATTREQInput, ATTREQCard,
  ATTREQChip, ATTREQPill, ATTREQGarment, ATTREQBtn,
  IconSun, IconShirt, IconBook, IconPerson, IconCamera, IconImage,
  IconLocation, IconSearch, IconBell, IconChevron, IconSparkles,
  IconBack, IconCheck, IconHeart, IconMenu, IconX,
})
