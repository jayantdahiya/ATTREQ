// ATTREQ Main App screens — Dashboard, Wardrobe, History, Profile

function ATTREQWeatherStrip() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'11px 14px', borderRadius:14, background:C.surface, border:`1px solid ${C.border}`, marginBottom:18 }}>
      <div style={{ display:'flex', alignItems:'center', gap:6 }}>
        <IconLocation size={12} color={C.t3}/>
        <span style={{ fontFamily:F.body, fontSize:13, color:C.t2 }}>Milan, IT</span>
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <span style={{ fontFamily:F.display, fontSize:20, fontWeight:600, color:C.text }}>22°</span>
        <div style={{ width:1, height:14, background:C.border }}/>
        <ATTREQML>Partly cloudy</ATTREQML>
      </div>
    </div>
  )
}

function ATTREQRecoCard() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <ATTREQCard style={{ padding:16 }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:14 }}>
        <div>
          <ATTREQML color={C.accent} style={{ display:'block', marginBottom:3 }}>Look No. 01</ATTREQML>
          <div style={{ fontFamily:F.display, fontSize:22, fontWeight:600, fontStyle:'italic', color:C.text }}>The Long Walk</div>
        </div>
        <ATTREQPill variant="muted">87% match</ATTREQPill>
      </div>

      <div style={{ display:'flex', gap:8, height:190, marginBottom:12 }}>
        <ATTREQGarment tone="top"    style={{ flex:'0 0 54%', height:'100%', borderRadius:16 }} label="Top"/>
        <div style={{ flex:1, display:'flex', flexDirection:'column', gap:8 }}>
          <ATTREQGarment tone="bottom" style={{ flex:'0 0 57%', borderRadius:16 }} label="Bottom"/>
          <ATTREQGarment tone="accent" style={{ flex:1, borderRadius:16 }} label="Accent"/>
        </div>
      </div>

      <div style={{ display:'flex', gap:10, marginBottom:11 }}>
        <ATTREQML>22°C — Partly Cloudy</ATTREQML>
        <ATTREQML color={C.accent}>— Casual</ATTREQML>
      </div>
      <div style={{ height:1, background:C.borderSoft, marginBottom:11 }}/>

      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:11 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ display:'flex', alignItems:'center', gap:4, cursor:'pointer' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={C.t3} strokeWidth="2" strokeLinecap="round"><path d="m19 12H5M5 12l7-7M5 12l7 7"/></svg>
            <ATTREQML>Skip</ATTREQML>
          </div>
          <div style={{ width:1, height:11, background:C.border }}/>
          <div style={{ display:'flex', alignItems:'center', gap:4, cursor:'pointer' }}>
            <ATTREQML color={C.moss}>Wear</ATTREQML>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={C.moss} strokeWidth="2" strokeLinecap="round"><path d="m5 12h14M19 12l-7-7M19 12l-7 7"/></svg>
          </div>
        </div>
        <div style={{ display:'flex', gap:6 }}>
          <div style={{ width:33, height:33, borderRadius:100, border:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
            <IconHeart size={13} color={C.accent}/>
          </div>
          <div style={{ width:33, height:33, borderRadius:100, background:C.accentSoft, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
            <IconX size={13} color={C.t2}/>
          </div>
        </div>
      </div>

      <ATTREQBtn>
        <IconCheck size={13} color="currentColor"/>
        Wear this
      </ATTREQBtn>
    </ATTREQCard>
  )
}

function ATTREQDashboard() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'10px 24px', height:'calc(100% - 44px)', boxSizing:'border-box', position:'relative', overflow:'hidden' }}>
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:16 }}>
          <div>
            <ATTREQML style={{ display:'block', marginBottom:5 }}>Monday 23/06</ATTREQML>
            <div style={{ fontFamily:F.display, fontSize:32, fontWeight:600, lineHeight:1.1, color:C.text }}>
              Good morning,<br/><span style={{ fontStyle:'italic', color:C.accent }}>Natasha.</span>
            </div>
          </div>
          <div style={{ width:34, height:34, borderRadius:100, border:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', marginTop:22, cursor:'pointer', flexShrink:0 }}>
            <IconMenu size={15} color={C.t2}/>
          </div>
        </div>

        <ATTREQWeatherStrip/>

        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:13 }}>
          <span style={{ fontFamily:F.display, fontSize:20, fontStyle:'italic', fontWeight:600, color:C.text }}>Today's looks</span>
          <ATTREQML>3 looks</ATTREQML>
        </div>

        <ATTREQRecoCard/>

        <ATTREQCard style={{ padding:'11px 15px', marginTop:11 }}>
          <ATTREQML style={{ letterSpacing:'1.1px' }}>Pull down to weave new looks from weather, wardrobe and feedback.</ATTREQML>
        </ATTREQCard>

        <ATTREQTabBar active={0}/>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQWardrobe() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  const cats = ['All','Tops','Bottoms','Outer','Accents','Shoes']
  const col1 = [
    { tone:'top',    cat:'Top',     color:'Cream Linen',    h:208 },
    { tone:'outer',  cat:'Outer',   color:'Camel Coat',     h:174 },
    { tone:'accent', cat:'Scarf',   color:'Olive Silk',     h:146 },
  ]
  const col2 = [
    { tone:'bottom', cat:'Bottom',  color:'Navy Wool',      h:172 },
    { tone:'top',    cat:'Top',     color:'White Cotton',   h:190 },
    { tone:'bottom', cat:'Bottom',  color:'Charcoal Tweed', h:186 },
  ]
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'10px 24px', height:'calc(100% - 44px)', boxSizing:'border-box', position:'relative', overflow:'hidden' }}>
        <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:3 }}>
          <div>
            <ATTREQML style={{ display:'block', marginBottom:5 }}>Closet</ATTREQML>
            <div style={{ fontFamily:F.display, fontSize:28, fontWeight:600, fontStyle:'italic', color:C.text }}>Wardrobe</div>
          </div>
          <div style={{ width:34, height:34, borderRadius:100, border:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', marginTop:16 }}>
            <IconSearch size={14} color={C.t2}/>
          </div>
        </div>
        <ATTREQBody style={{ marginBottom:12, fontSize:13 }}>
          <span style={{ color:C.accent, fontWeight:500 }}>24 pieces</span>
          <span style={{ color:C.t3 }}> — last added today</span>
        </ATTREQBody>

        <div style={{ display:'flex', gap:6, marginBottom:12, overflow:'hidden' }}>
          {cats.map((c, i) => (
            <div key={c} style={{ flexShrink:0, padding:'5px 12px', borderRadius:100, background: i===0 ? C.text : 'transparent', border:`1px solid ${i===0 ? C.text : C.border}`, fontFamily:F.body, fontSize:12, fontWeight:500, color: i===0 ? C.bg : C.t2, cursor:'pointer' }}>{c}</div>
          ))}
        </div>

        <div style={{ display:'flex', gap:9, marginBottom:14 }}>
          {[{ Icon:IconCamera, label:'Camera', sub:'Capture a piece' }, { Icon:IconImage, label:'Library', sub:'From photos' }].map(({ Icon, label, sub }) => (
            <div key={label} style={{ flex:1, padding:'12px 13px', borderRadius:16, border:`1.5px dashed ${C.border}`, background:C.surface, cursor:'pointer', display:'flex', flexDirection:'column', gap:5 }}>
              <div style={{ width:28, height:28, borderRadius:100, background:C.accentSoft, display:'flex', alignItems:'center', justifyContent:'center' }}>
                <Icon size={13} color={C.t2}/>
              </div>
              <div style={{ fontFamily:F.body, fontSize:13, fontWeight:500, color:C.text }}>{label}</div>
              <ATTREQML>{sub}</ATTREQML>
            </div>
          ))}
        </div>

        <div style={{ display:'flex', gap:10 }}>
          {[col1, col2].map((col, ci) => (
            <div key={ci} style={{ flex:1, display:'flex', flexDirection:'column', gap:10 }}>
              {col.map((item, idx) => (
                <div key={idx}>
                  <ATTREQGarment tone={item.tone} style={{ height:item.h, borderRadius:16, width:'100%' }}/>
                  <div style={{ paddingTop:6, paddingLeft:1 }}>
                    <div style={{ fontFamily:F.display, fontSize:13, fontStyle:'italic', fontWeight:600, color:C.text }}>{item.cat}</div>
                    <ATTREQML>{item.color}</ATTREQML>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        <ATTREQTabBar active={1}/>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQHistory() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  const groups = [
    { date:'Monday 06/23', key:'2025-06-23', outfits:[
      { name:'The Long Walk', pieces:3, status:'Worn',   variant:'moss' },
      { name:'Casual Friday', pieces:3, status:'Loved',  variant:'gold' },
    ]},
    { date:'Sunday 06/22', key:'2025-06-22', outfits:[
      { name:'Evening Edit',  pieces:3, status:'Loved',  variant:'gold' },
      { name:'Morning Run',   pieces:3, status:'Skipped',variant:'clay' },
    ]},
  ]
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'10px 24px', height:'calc(100% - 44px)', boxSizing:'border-box', position:'relative', overflow:'hidden' }}>
        <div style={{ marginBottom:20 }}>
          <ATTREQML style={{ display:'block', marginBottom:5 }}>Diary</ATTREQML>
          <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between' }}>
            <div style={{ fontFamily:F.display, fontSize:28, fontWeight:600, fontStyle:'italic', color:C.text }}>History</div>
            <ATTREQML>18 looks tracked</ATTREQML>
          </div>
        </div>
        {groups.map(group => (
          <div key={group.key} style={{ marginBottom:20 }}>
            <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:10 }}>
              <div style={{ fontFamily:F.display, fontSize:16, fontStyle:'italic', fontWeight:600, color:C.text, whiteSpace:'nowrap' }}>{group.date}</div>
              <div style={{ flex:1, height:1, background:C.borderSoft }}/>
              <ATTREQML>{group.key}</ATTREQML>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {group.outfits.map((outfit, i) => (
                <ATTREQCard key={i} style={{ padding:'11px 14px', display:'flex', gap:10, alignItems:'center' }}>
                  <div style={{ display:'flex', gap:3, flexShrink:0 }}>
                    {['top','bottom','accent'].map(t => (
                      <ATTREQGarment key={t} tone={t} style={{ width:34, height:50, borderRadius:9 }}/>
                    ))}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontFamily:F.display, fontSize:15, fontStyle:'italic', fontWeight:600, color:C.text, marginBottom:2 }}>{outfit.name}</div>
                    <ATTREQML>{outfit.pieces} pieces</ATTREQML>
                  </div>
                  <ATTREQPill variant={outfit.variant}>{outfit.status}</ATTREQPill>
                </ATTREQCard>
              ))}
            </div>
          </div>
        ))}
        <ATTREQTabBar active={2}/>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQProfile() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  const prefs = [
    { Icon:IconLocation, label:'Milan, Italy',       sub:'Coordinates saved',       action:'Edit'  },
    { Icon:IconBell,     label:'Daily reminder',     sub:'8:00 AM — weekdays',      toggle:true    },
    { Icon:IconSparkles, label:'Style preferences',  sub:'Minimal — Earthy — Layered', action:'Edit' },
  ]
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'10px 24px', height:'calc(100% - 44px)', boxSizing:'border-box', position:'relative', overflow:'hidden' }}>
        <div style={{ marginBottom:18 }}>
          <ATTREQML style={{ display:'block', marginBottom:5 }}>You</ATTREQML>
          <div style={{ fontFamily:F.display, fontSize:28, fontWeight:600, fontStyle:'italic', color:C.text }}>Profile</div>
        </div>

        <ATTREQCard style={{ padding:'18px 20px', marginBottom:18, borderLeft:`3px solid ${C.accent}` }}>
          <div style={{ display:'flex', alignItems:'center', gap:14, marginBottom:14 }}>
            <div style={{ width:50, height:50, borderRadius:100, background:C.accent, display:'flex', alignItems:'center', justifyContent:'center', fontFamily:F.display, fontSize:19, fontStyle:'italic', fontWeight:600, color:C.bg, flexShrink:0 }}>NA</div>
            <div>
              <div style={{ fontFamily:F.display, fontSize:20, fontWeight:600, color:C.text }}>Natasha A.</div>
              <ATTREQBody style={{ fontSize:13 }}>natasha@attreq.com</ATTREQBody>
            </div>
          </div>
          <div style={{ height:1, background:C.borderSoft, marginBottom:14 }}/>
          <div style={{ display:'flex', gap:28 }}>
            {[{l:'Pieces',v:'24'},{l:'Worn',v:'12'},{l:'Streak',v:'3d',accent:true}].map(s => (
              <div key={s.l}>
                <ATTREQML style={{ display:'block', marginBottom:3 }}>{s.l}</ATTREQML>
                <div style={{ fontFamily:F.display, fontSize:22, fontWeight:600, fontStyle:'italic', color: s.accent ? C.accent : C.text }}>{s.v}</div>
              </div>
            ))}
          </div>
        </ATTREQCard>

        <ATTREQML style={{ display:'block', marginBottom:8 }}>Style DNA</ATTREQML>
        <ATTREQCard style={{ padding:0, overflow:'hidden', marginBottom:18 }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, padding:'13px 16px', cursor:'pointer' }}>
            <IconSparkles size={15} color={C.t2}/>
            <div style={{ flex:1 }}>
              <div style={{ fontFamily:F.body, fontSize:14, color:C.text }}>Your Style DNA</div>
              <ATTREQML>Tap to view or edit</ATTREQML>
            </div>
            <IconChevron size={13} color={C.t3}/>
          </div>
        </ATTREQCard>

        <ATTREQML style={{ display:'block', marginBottom:8 }}>Preferences</ATTREQML>
        <ATTREQCard style={{ padding:0, overflow:'hidden' }}>
          {prefs.map((row, i) => {
            const { Icon } = row
            return (
              <div key={i} style={{ display:'flex', alignItems:'center', gap:12, padding:'12px 16px', borderBottom: i < prefs.length-1 ? `1px solid ${C.borderSoft}` : 'none', cursor:'pointer' }}>
                <Icon size={15} color={C.t2}/>
                <div style={{ flex:1 }}>
                  <div style={{ fontFamily:F.body, fontSize:13, color:C.text }}>{row.label}</div>
                  <ATTREQML>{row.sub}</ATTREQML>
                </div>
                {row.toggle
                  ? <div style={{ width:36, height:20, borderRadius:100, background:C.moss, display:'flex', alignItems:'center', padding:'0 2px', justifyContent:'flex-end' }}><div style={{ width:16, height:16, borderRadius:100, background:C.bg }}/></div>
                  : row.action ? <ATTREQML color={C.accent}>{row.action}</ATTREQML> : <IconChevron size={13} color={C.t3}/>
                }
              </div>
            )
          })}
        </ATTREQCard>

        <div style={{ textAlign:'center', marginTop:18 }}>
          <ATTREQML color={C.clay} style={{ cursor:'pointer', letterSpacing:'1.2px' }}>Sign out</ATTREQML>
          <div style={{ marginTop:7 }}><ATTREQML color={C.t3} style={{ letterSpacing:'0.8px' }}>v 1.4.2 — ATTREQ</ATTREQML></div>
        </div>

        <ATTREQTabBar active={3}/>
      </div>
    </ATTREQScreen>
  )
}

Object.assign(window, {
  ATTREQWeatherStrip, ATTREQRecoCard,
  ATTREQDashboard, ATTREQWardrobe, ATTREQHistory, ATTREQProfile,
})
