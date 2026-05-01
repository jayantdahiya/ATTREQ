// ATTREQ design tokens — earthy, editorial, warm
const ATTREQ_TOKENS = {
  dark: {
    bgDeep: '#0D1210',
    bgSurface: '#151E1A',
    bgRaised: '#1C2923',
    bgSunk: '#0A0E0C',
    moss: '#36664A',
    mossSoft: 'rgba(54,102,74,0.20)',
    mossGlow: 'rgba(54,102,74,0.08)',
    olive: '#6F8B57',
    gold: '#D4A854',
    goldSoft: 'rgba(212,168,84,0.22)',
    goldGlow: 'rgba(212,168,84,0.06)',
    clay: '#C9604A',
    text: '#F0EDE6',
    textSec: '#9B978E',
    textTer: '#5C5850',
    border: '#252E28',
    borderSoft: 'rgba(240,237,230,0.06)',
  },
  light: {
    bgDeep: '#F0EBE1',
    bgSurface: '#F7F3EC',
    bgRaised: '#FFFFFF',
    bgSunk: '#E8E2D5',
    moss: '#2F5A40',
    mossSoft: 'rgba(47,90,64,0.14)',
    mossGlow: 'rgba(47,90,64,0.04)',
    olive: '#5A7344',
    gold: '#A8842F',
    goldSoft: 'rgba(168,132,47,0.20)',
    goldGlow: 'rgba(168,132,47,0.05)',
    clay: '#A8492F',
    text: '#1F2420',
    textSec: '#6E6A60',
    textTer: '#9D998F',
    border: 'rgba(31,36,32,0.10)',
    borderSoft: 'rgba(31,36,32,0.06)',
  },
};

// Typography stacks
const FONT_DISPLAY = '"Cormorant Garamond", "EB Garamond", Georgia, serif';
const FONT_BODY = '"DM Sans", "Inter", -apple-system, system-ui, sans-serif';
const FONT_MONO = '"IBM Plex Mono", "JetBrains Mono", ui-monospace, monospace';

// Subtle SVG grain — barely perceptible noise on bgDeep
const GRAIN_SVG = encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' seed='3'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.16 0'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.55'/></svg>`);
const GRAIN_URL = `url("data:image/svg+xml,${GRAIN_SVG}")`;

// Paper-grain — softer, used on cards
const PAPER_SVG = encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='p'><feTurbulence type='fractalNoise' baseFrequency='1.2' numOctaves='1' seed='7'/><feColorMatrix values='0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.05 0'/></filter><rect width='100%' height='100%' filter='url(%23p)'/></svg>`);
const PAPER_URL = `url("data:image/svg+xml,${PAPER_SVG}")`;

// Garment placeholder — striped fabric-suggestion panel
function Garment({ tone = 'top', label, ratio = '4/5', radius = 14, t, style = {}, mono = true }) {
  // Each garment type has its own distinct hue/saturation, all earthy
  const tones = {
    top:    { a: '#3A4A3E', b: '#2A3A2E', accent: '#6F8B57' },  // olive
    bottom: { a: '#2A2620', b: '#1A1612', accent: '#8A6F4A' },  // brown
    accent: { a: '#5A3E2E', b: '#4A2E1E', accent: '#C9604A' },  // clay
    shoes:  { a: '#1A1A18', b: '#0A0A08', accent: '#5C5850' },  // black
    outer:  { a: '#3E3A30', b: '#2E2A20', accent: '#D4A854' },  // gold
    bag:    { a: '#4A3E2A', b: '#3A2E1A', accent: '#A8842F' },  // tan
  };
  const sw = tones[tone] || tones.top;
  return (
    <div style={{
      aspectRatio: ratio,
      borderRadius: radius,
      background: `linear-gradient(135deg, ${sw.a}, ${sw.b})`,
      position: 'relative', overflow: 'hidden',
      boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.04)',
      ...style,
    }}>
      {/* Diagonal weave stripes */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 7px)`,
      }}/>
      {/* Vignette */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.06), transparent 60%)',
      }}/>
      {/* Accent dot */}
      <div style={{
        position: 'absolute', top: 10, right: 10,
        width: 6, height: 6, borderRadius: 3, background: sw.accent, opacity: 0.7,
      }}/>
      {label && mono && (
        <div style={{
          position: 'absolute', bottom: 8, left: 10,
          fontFamily: FONT_MONO, fontSize: 8.5, letterSpacing: '0.15em',
          color: 'rgba(240,237,230,0.55)', textTransform: 'uppercase',
        }}>{label}</div>
      )}
    </div>
  );
}

// Mono label pill
function MonoLabel({ children, color, style = {} }) {
  return (
    <span style={{
      fontFamily: FONT_MONO, fontSize: 10, letterSpacing: '0.18em',
      textTransform: 'uppercase', color: color || 'currentColor',
      ...style,
    }}>{children}</span>
  );
}

Object.assign(window, { ATTREQ_TOKENS, FONT_DISPLAY, FONT_BODY, FONT_MONO, GRAIN_URL, PAPER_URL, Garment, MonoLabel });
