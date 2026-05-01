// ATTREQ — Auth screens (Login + Registration)

function AttreqAuthInput({ t, label, value, type = 'text', focused = false }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{
        fontFamily: FONT_MONO, fontSize: 9.5, letterSpacing: '0.2em',
        textTransform: 'uppercase', color: focused ? t.gold : t.textTer,
        marginBottom: 8,
      }}>{label}</div>
      <div style={{
        borderBottom: `1px solid ${focused ? t.gold : t.border}`,
        paddingBottom: 9,
        display: 'flex', alignItems: 'center',
      }}>
        <div style={{
          fontFamily: FONT_BODY, fontSize: 16, color: value ? t.text : t.textTer,
          flex: 1,
        }}>{value || '\u00A0'}</div>
        {type === 'password' && value && (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={t.textSec} strokeWidth="1.6">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        )}
      </div>
    </div>
  );
}

function AttreqLogin({ t }) {
  return (
    <PhoneBg t={t}>
      {/* Atmospheric texture top */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 380,
        background: `linear-gradient(180deg, ${t.bgSurface} 0%, ${t.bgDeep} 100%)`,
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: `radial-gradient(ellipse at 50% 30%, ${t.goldGlow}, transparent 60%)`,
        }}/>
        {/* fabric weave hint */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `repeating-linear-gradient(45deg, rgba(212,168,84,0.018) 0px, rgba(212,168,84,0.018) 1px, transparent 1px, transparent 6px)`,
        }}/>
      </div>

      <div style={{ position: 'relative', height: '100%', padding: '0 28px', display: 'flex', flexDirection: 'column' }}>
        <StatusSpacer/>

        {/* Wordmark area */}
        <div style={{ paddingTop: 56, textAlign: 'center' }}>
          <div style={{
            fontFamily: FONT_MONO, fontSize: 9, letterSpacing: '0.4em',
            color: t.textTer, marginBottom: 18, textTransform: 'uppercase',
          }}>est. 2026 — personal styling</div>
          <div style={{
            fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 56,
            color: t.gold, letterSpacing: '0.08em',
            lineHeight: 1,
          }}>ATTREQ</div>
          <div style={{
            fontFamily: FONT_DISPLAY, fontStyle: 'italic', fontSize: 17,
            color: t.textSec, marginTop: 12,
          }}>Your closet, curated.</div>
        </div>

        {/* Card */}
        <div style={{
          marginTop: 70,
          background: t.bgSurface,
          borderRadius: 28,
          border: `1px solid ${t.borderSoft}`,
          padding: '32px 26px 26px',
          boxShadow: `0 24px 48px rgba(0,0,0,0.4), 0 0 0 1px ${t.goldGlow}`,
          position: 'relative',
        }}>
          {/* gold top accent */}
          <div style={{
            position: 'absolute', top: 0, left: '38%', right: '38%', height: 2,
            background: t.gold, borderRadius: '0 0 2px 2px',
          }}/>
          <div style={{
            fontFamily: FONT_DISPLAY, fontSize: 26, fontWeight: 600,
            color: t.text, letterSpacing: '-0.01em', marginBottom: 4,
          }}>Welcome back</div>
          <div style={{
            fontFamily: FONT_BODY, fontSize: 13, color: t.textSec, marginBottom: 28,
          }}>Sign in to your wardrobe.</div>

          <AttreqAuthInput t={t} label="Email" value="iris@attreq.app"/>
          <AttreqAuthInput t={t} label="Password" type="password" value="••••••••••" focused/>

          <button style={{
            width: '100%', marginTop: 20,
            background: t.moss, border: 'none', color: '#F0EDE6',
            fontFamily: FONT_BODY, fontSize: 15, fontWeight: 600,
            padding: '15px 0', borderRadius: 16,
            letterSpacing: '0.02em',
            boxShadow: `0 6px 16px rgba(54,102,74,0.32)`,
          }}>Sign in</button>

          <div style={{
            textAlign: 'center', marginTop: 16,
            fontFamily: FONT_MONO, fontSize: 10, letterSpacing: '0.18em',
            textTransform: 'uppercase', color: t.textTer,
          }}>Forgot password</div>
        </div>

        <div style={{ flex: 1 }}/>

        <div style={{
          textAlign: 'center', paddingBottom: 38,
          fontFamily: FONT_BODY, fontSize: 13, color: t.textSec,
        }}>
          New here? <span style={{ color: t.gold, fontWeight: 500 }}>Create account →</span>
        </div>
      </div>
    </PhoneBg>
  );
}

function AttreqRegister({ t }) {
  return (
    <PhoneBg t={t}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 280,
        background: `linear-gradient(180deg, ${t.bgSurface} 0%, ${t.bgDeep} 100%)`,
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: `radial-gradient(ellipse at 50% 20%, ${t.mossGlow}, transparent 60%)`,
        }}/>
      </div>

      <div style={{ position: 'relative', height: '100%', padding: '0 28px', display: 'flex', flexDirection: 'column' }}>
        <StatusSpacer/>

        {/* Back chevron */}
        <div style={{ paddingTop: 14, marginBottom: 20 }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={t.textSec} strokeWidth="1.8" strokeLinecap="round">
            <path d="M15 6l-6 6 6 6"/>
          </svg>
        </div>

        <div>
          <MonoLabel style={{ color: t.gold }}>01 — Begin</MonoLabel>
          <div style={{
            fontFamily: FONT_DISPLAY, fontWeight: 600, fontSize: 38,
            color: t.text, lineHeight: 1.05, marginTop: 14, letterSpacing: '-0.02em',
          }}>Make this<br/><span style={{ fontStyle: 'italic', color: t.gold }}>your closet.</span></div>
          <div style={{
            fontFamily: FONT_BODY, fontSize: 14, color: t.textSec,
            marginTop: 14, lineHeight: 1.5, maxWidth: 280,
          }}>A few details — then we'll learn your wardrobe and your weather, and meet you each morning.</div>
        </div>

        <div style={{
          marginTop: 38,
          background: t.bgSurface,
          borderRadius: 24,
          border: `1px solid ${t.borderSoft}`,
          padding: '26px 24px 22px',
        }}>
          <AttreqAuthInput t={t} label="Full name" value="Iris Andersen" focused/>
          <AttreqAuthInput t={t} label="Email" value="iris@attreq.app"/>
          <AttreqAuthInput t={t} label="Password" type="password" value="••••••••"/>

          <button style={{
            width: '100%', marginTop: 14,
            background: t.gold, border: 'none', color: '#1A1410',
            fontFamily: FONT_BODY, fontSize: 15, fontWeight: 600,
            padding: '15px 0', borderRadius: 16,
            letterSpacing: '0.02em',
          }}>Create account →</button>
        </div>

        <div style={{ flex: 1 }}/>

        <div style={{
          textAlign: 'center', paddingBottom: 38,
          fontFamily: FONT_BODY, fontSize: 12, color: t.textTer,
        }}>By continuing you accept our terms · privacy</div>
      </div>
    </PhoneBg>
  );
}

Object.assign(window, { AttreqLogin, AttreqRegister });
