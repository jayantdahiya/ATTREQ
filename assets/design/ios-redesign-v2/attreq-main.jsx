
// ATTREQ Main — design canvas with iOS frames + tweaks

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "noir",
  "showRegister": false,
  "showLocation": false
}/*EDITMODE-END*/;

// ── ATTREQApp: screen router ──────────────────────────────────────────────
function ATTREQApp({ theme, initialScreen }) {
  const t = window.THEMES[theme] || window.THEMES.noir;
  const [screen, setScreen] = React.useState(initialScreen || 'today');
  const prev = React.useRef(initialScreen);

  React.useEffect(() => {
    if (initialScreen !== prev.current) {
      setScreen(initialScreen);
      prev.current = initialScreen;
    }
  }, [initialScreen]);

  const LS   = window.LoginScreen;
  const RS   = window.RegisterScreen;
  const LP   = window.LocationPermScreen;
  const DS   = window.DashboardScreen;
  const WS   = window.WardrobeScreen;
  const HS   = window.HistoryScreen;
  const PS   = window.ProfileScreen;
  const TB   = window.TabBar;

  const content = (() => {
    switch (screen) {
      case 'login':    return <LS    t={t} onNavigate={setScreen} />;
      case 'register': return <RS    t={t} onNavigate={setScreen} />;
      case 'location': return <LP    t={t} onAllow={() => setScreen('today')} />;
      case 'today':    return <DS    t={t} />;
      case 'wardrobe': return <WS    t={t} />;
      case 'history':  return <HS    t={t} />;
      case 'profile':  return <PS    t={t} onNavigate={setScreen} />;
      default:         return <DS    t={t} />;
    }
  })();

  const showTabs = ['today','wardrobe','history','profile'].includes(screen);

  return (
    <div style={{ width:'100%', height:'100%', position:'relative', overflow:'hidden', background: t.bgDeep }}>
      {content}
      {showTabs && <TB active={screen} onTab={setScreen} t={t} />}
    </div>
  );
}

// ── Frame: IOSDevice wrapper ──────────────────────────────────────────────
function Frame({ theme, initialScreen, statusBarStyle }) {
  const Dev = window.IOSDevice;
  const dark = statusBarStyle === 'light';
  return (
    <Dev dark={dark}>
      <ATTREQApp theme={theme} initialScreen={initialScreen} />
    </Dev>
  );
}

// ── Main canvas ───────────────────────────────────────────────────────────
function ATTREQMain() {
  const [tweaks, setTweak] = window.useTweaks(TWEAK_DEFAULTS);

  const leftAuth = tweaks.showLocation ? 'location'
                 : tweaks.showRegister  ? 'register'
                 : 'login';

  const DC   = window.DesignCanvas;
  const Sec  = window.DCSection;
  const AB   = window.DCArtboard;
  const TP   = window.TweaksPanel;
  const TSec = window.TweakSection;
  const TR   = window.TweakRadio;
  const TT   = window.TweakToggle;

  return (
    <>
      <DC>
        {/* ── Auth & Dashboard ── */}
        <Sec id="auth-dash" title="Auth & Dashboard">
          <AB id="noir-login"  label="Login — Noir"       width={390} height={844}>
            <Frame theme="noir"  initialScreen={leftAuth} statusBarStyle="light" />
          </AB>
          <AB id="noir-today"  label="Dashboard — Noir"   width={390} height={844}>
            <Frame theme="noir"  initialScreen="today"    statusBarStyle="light" />
          </AB>
          <AB id="cream-login" label="Login — Cream"      width={390} height={844}>
            <Frame theme="cream" initialScreen={leftAuth} statusBarStyle="dark" />
          </AB>
          <AB id="cream-today" label="Dashboard — Cream"  width={390} height={844}>
            <Frame theme="cream" initialScreen="today"    statusBarStyle="dark" />
          </AB>
          <AB id="slate-today" label="Dashboard — Slate"  width={390} height={844}>
            <Frame theme="slate" initialScreen="today"    statusBarStyle="dark" />
          </AB>
        </Sec>

        {/* ── Wardrobe & History ── */}
        <Sec id="wardrobe-history" title="Wardrobe & History">
          <AB id="noir-wardrobe"  label="Wardrobe — Noir"   width={390} height={844}>
            <Frame theme="noir"  initialScreen="wardrobe"  statusBarStyle="light" />
          </AB>
          <AB id="cream-wardrobe" label="Wardrobe — Cream"  width={390} height={844}>
            <Frame theme="cream" initialScreen="wardrobe"  statusBarStyle="dark" />
          </AB>
          <AB id="slate-wardrobe" label="Wardrobe — Slate"  width={390} height={844}>
            <Frame theme="slate" initialScreen="wardrobe"  statusBarStyle="dark" />
          </AB>
          <AB id="noir-history"   label="History — Noir"    width={390} height={844}>
            <Frame theme="noir"  initialScreen="history"   statusBarStyle="light" />
          </AB>
          <AB id="cream-history"  label="History — Cream"   width={390} height={844}>
            <Frame theme="cream" initialScreen="history"   statusBarStyle="dark" />
          </AB>
        </Sec>

        {/* ── Profile & Onboarding ── */}
        <Sec id="profile-onboard" title="Profile & Onboarding">
          <AB id="noir-profile"   label="Profile — Noir"            width={390} height={844}>
            <Frame theme="noir"  initialScreen="profile"            statusBarStyle="light" />
          </AB>
          <AB id="cream-profile"  label="Profile — Cream"           width={390} height={844}>
            <Frame theme="cream" initialScreen="profile"            statusBarStyle="dark" />
          </AB>
          <AB id="noir-register"  label="Register — Noir"           width={390} height={844}>
            <Frame theme="noir"  initialScreen="register"           statusBarStyle="light" />
          </AB>
          <AB id="cream-register" label="Register — Cream"          width={390} height={844}>
            <Frame theme="cream" initialScreen="register"           statusBarStyle="dark" />
          </AB>
          <AB id="noir-location"  label="Location Onboarding — Noir" width={390} height={844}>
            <Frame theme="noir"  initialScreen="location"           statusBarStyle="light" />
          </AB>
          <AB id="slate-profile"  label="Profile — Slate"           width={390} height={844}>
            <Frame theme="slate" initialScreen="profile"            statusBarStyle="dark" />
          </AB>
        </Sec>
      </DC>

      <TP>
        <TSec label="Color theme">
          <TR
            label="Theme"
            value={tweaks.theme}
            onChange={(v) => setTweak('theme', v)}
            options={[
              { value: 'noir',  label: 'Noir'  },
              { value: 'cream', label: 'Cream' },
              { value: 'slate', label: 'Slate' },
            ]}
          />
        </TSec>
        <TSec label="Auth screens">
          <TT label="Show register"  value={tweaks.showRegister} onChange={(v) => setTweak('showRegister', v)} />
          <TT label="Show location"  value={tweaks.showLocation} onChange={(v) => setTweak('showLocation', v)} />
        </TSec>
      </TP>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<ATTREQMain />);
