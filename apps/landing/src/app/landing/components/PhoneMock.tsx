const stroke = { fill: 'none', strokeWidth: 1.5, strokeLinecap: 'round' as const };

function IconLocation({ size = 12 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke}>
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function IconMenu({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function IconCheck({ size = 12 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke} strokeWidth={2.2}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function IconSun({ size = 17 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke}>
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="5" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="2" y1="12" x2="5" y2="12" />
      <line x1="19" y1="12" x2="22" y2="12" />
      <line x1="4.22" y1="4.22" x2="6.34" y2="6.34" />
      <line x1="17.66" y1="17.66" x2="19.78" y2="19.78" />
      <line x1="4.22" y1="19.78" x2="6.34" y2="17.66" />
      <line x1="17.66" y1="6.34" x2="19.78" y2="4.22" />
    </svg>
  );
}

function IconShirt({ size = 17 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke} strokeLinejoin="round">
      <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z" />
    </svg>
  );
}

function IconBook({ size = 17 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke}>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );
}

function IconPerson({ size = 17 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" stroke="currentColor" {...stroke}>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

const tabs = [
  { label: 'TODAY', Icon: IconSun, active: true },
  { label: 'WARDROBE', Icon: IconShirt, active: false },
  { label: 'HISTORY', Icon: IconBook, active: false },
  { label: 'PROFILE', Icon: IconPerson, active: false },
];

export function PhoneMock() {
  return (
    <div className="phone" role="img" aria-label="The ATTREQ app showing today's outfit recommendation: a look named The Long Walk with an 87% match for 22 degrees and partly cloudy weather">
      <div className="phone__screen">
        <div className="phone__statusbar" aria-hidden="true">
          <span>9:41</span>
          <svg width="25" height="11" viewBox="0 0 25 11">
            <rect x="0.5" y="0.5" width="21" height="10" rx="3" stroke="currentColor" strokeOpacity="0.3" fill="none" />
            <rect x="2" y="2" width="16.5" height="7" rx="1.5" fill="currentColor" />
            <path d="M22.5 3.5v4a2 2 0 0 0 0-4z" fill="currentColor" fillOpacity="0.4" />
          </svg>
        </div>

        <div className="phone__greeting-row">
          <div>
            <span className="phone__ml">Monday 23/06</span>
            <div className="phone__greeting">
              Good morning,
              <br />
              <span className="landing-em">Natasha.</span>
            </div>
          </div>
          <div className="phone__menu-dot">
            <IconMenu />
          </div>
        </div>

        <div className="phone__weather">
          <span className="phone__weather-place">
            <span style={{ color: 'var(--ink-3)', display: 'inline-flex' }}>
              <IconLocation />
            </span>
            Milan, IT
          </span>
          <span className="phone__weather-temp">
            <span className="phone__temp">22°</span>
            <span className="phone__vr" />
            <span className="phone__ml">Partly cloudy</span>
          </span>
        </div>

        <div className="phone__looks-row">
          <span className="phone__looks-title">Today&rsquo;s looks</span>
          <span className="phone__ml">3 looks</span>
        </div>

        <div className="phone__card">
          <div className="phone__card-head">
            <div>
              <span className="phone__ml" style={{ color: 'var(--bronze)' }}>
                Look No. 01
              </span>
              <div className="phone__look-name">The Long Walk</div>
            </div>
            <span className="phone__pill">87% match</span>
          </div>

          <div className="phone__garments">
            <div className="phone__garment phone__garment--top">
              <span className="phone__garment-label">Top</span>
            </div>
            <div className="phone__garment-col">
              <div className="phone__garment phone__garment--bottom">
                <span className="phone__garment-label">Bottom</span>
              </div>
              <div className="phone__garment phone__garment--accent">
                <span className="phone__garment-label">Accent</span>
              </div>
            </div>
          </div>

          <div className="phone__card-meta">
            <span className="phone__ml">22°C — Partly cloudy</span>
            <span className="phone__ml" style={{ color: 'var(--bronze)' }}>
              — Casual
            </span>
          </div>
          <div className="phone__divider" />

          <div className="phone__btn">
            <IconCheck />
            Wear this
          </div>
        </div>

        <div className="phone__tabbar" aria-hidden="true">
          {tabs.map(({ label, Icon, active }) => (
            <span key={label} className={active ? 'phone__tab phone__tab--active' : 'phone__tab'}>
              <Icon />
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
