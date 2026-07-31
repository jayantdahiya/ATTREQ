// ATTREQ Auth screens — Login + Register (3 steps)

function ATTREQStepNav({ step, total=3 }) {
  const { C } = useATTREQTheme()
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:26 }}>
      <div style={{ width:30, height:30, borderRadius:100, border:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', flexShrink:0 }}>
        <IconBack color={C.t2}/>
      </div>
      <div style={{ display:'flex', gap:5, alignItems:'center' }}>
        {Array.from({ length:total }, (_,i) => (
          <div key={i} style={{ height:3, borderRadius:100, width: i===step ? 22 : 8, background: i<=step ? C.text : C.border }}/>
        ))}
      </div>
      <ATTREQML>{String(step+1).padStart(2,'0')}/{String(total).padStart(2,'0')}</ATTREQML>
    </div>
  )
}

function ATTREQLogin() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'0 28px 40px', display:'flex', flexDirection:'column', height:'calc(100% - 44px)', justifyContent:'space-between' }}>

        <div style={{ textAlign:'center', paddingTop:42 }}>
          <div style={{ display:'flex', alignItems:'center', gap:14, justifyContent:'center', marginBottom:24 }}>
            <div style={{ flex:1, height:1, background:C.border }}/>
            <ATTREQML>Est. 2026 — Personal Styling</ATTREQML>
            <div style={{ flex:1, height:1, background:C.border }}/>
          </div>
          <div style={{ fontFamily:F.display, fontSize:60, letterSpacing:9, fontWeight:600, color:C.text, lineHeight:1, marginBottom:14 }}>ATTREQ</div>
          <div style={{ fontFamily:F.display, fontSize:19, fontStyle:'italic', color:C.t2, letterSpacing:0.3 }}>Your closet, curated.</div>
        </div>

        <ATTREQCard style={{ padding:'28px 24px' }}>
          <div style={{ fontFamily:F.display, fontSize:24, fontWeight:600, color:C.text, marginBottom:4 }}>Welcome back</div>
          <ATTREQBody style={{ marginBottom:24, fontSize:13 }}>Sign in to your wardrobe.</ATTREQBody>
          <div style={{ display:'flex', flexDirection:'column', gap:20, marginBottom:24 }}>
            <ATTREQInput label="Email address" value="hi@natasha.com"/>
            <ATTREQInput label="Password" value="••••••••••"/>
          </div>
          <ATTREQBtn>Sign in</ATTREQBtn>
          <div style={{ textAlign:'center', marginTop:14 }}>
            <ATTREQML style={{ cursor:'pointer', letterSpacing:'1.4px' }}>Forgot password</ATTREQML>
          </div>
        </ATTREQCard>

        <div style={{ textAlign:'center' }}>
          <ATTREQBody style={{ fontSize:13 }}>
            New here?{' '}
            <span style={{ color:C.accent, fontWeight:500, cursor:'pointer' }}>Create account</span>
          </ATTREQBody>
        </div>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQRegisterAccount() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'8px 28px 32px', height:'calc(100% - 44px)', boxSizing:'border-box', display:'flex', flexDirection:'column' }}>
        <ATTREQStepNav step={0}/>
        <ATTREQML color={C.accent} style={{ display:'block', marginBottom:8 }}>Step 01 — Account</ATTREQML>
        <div style={{ fontFamily:F.display, fontSize:36, fontWeight:600, lineHeight:1.1, color:C.text, marginBottom:6 }}>
          Make this<br/><span style={{ fontStyle:'italic', color:C.accent }}>your closet.</span>
        </div>
        <ATTREQBody style={{ marginBottom:20 }}>A few details, then we'll curate every look.</ATTREQBody>
        <ATTREQCard style={{ padding:'22px 20px', flex:1, display:'flex', flexDirection:'column', justifyContent:'center' }}>
          <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
            <ATTREQInput label="Email address" value="hi@natasha.com"/>
            <ATTREQInput label="Full name" value="Natasha A."/>
            <ATTREQInput label="Password" value="••••••••••"/>
            <ATTREQInput label="Confirm password" value="••••••••••"/>
          </div>
        </ATTREQCard>
        <div style={{ marginTop:16 }}><ATTREQBtn>Continue →</ATTREQBtn></div>
        <div style={{ textAlign:'center', marginTop:12 }}>
          <ATTREQBody style={{ fontSize:13 }}>
            Have an account?{' '}<span style={{ color:C.accent, fontWeight:500 }}>Sign in</span>
          </ATTREQBody>
        </div>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQRegisterStyle() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  const opts = ['Minimal','Earthy','Tailored','Layered','Casual','Formal','Streetwear','Athleisure']
  const sel  = ['Minimal','Earthy','Layered']
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'8px 28px 32px', height:'calc(100% - 44px)', boxSizing:'border-box', display:'flex', flexDirection:'column' }}>
        <ATTREQStepNav step={1}/>
        <ATTREQML color={C.accent} style={{ display:'block', marginBottom:8 }}>Step 02 — Style</ATTREQML>
        <div style={{ fontFamily:F.display, fontSize:36, fontWeight:600, lineHeight:1.1, color:C.text, marginBottom:6 }}>
          Define your<br/><span style={{ fontStyle:'italic', color:C.accent }}>aesthetic.</span>
        </div>
        <ATTREQBody style={{ marginBottom:20 }}>Tell us how you dress. We'll learn the rest.</ATTREQBody>
        <ATTREQCard style={{ padding:'22px 20px', flex:1 }}>
          <ATTREQML style={{ display:'block', marginBottom:14 }}>Style keywords</ATTREQML>
          <div style={{ display:'flex', flexWrap:'wrap', gap:7, marginBottom:20 }}>
            {opts.map(s => <ATTREQChip key={s} selected={sel.includes(s)}>{s}</ATTREQChip>)}
          </div>
          <div style={{ height:1, background:C.borderSoft, marginBottom:20 }}/>
          <ATTREQInput label="Occasions (optional)" value="Work, weekend, travel…"/>
        </ATTREQCard>
        <div style={{ marginTop:16 }}><ATTREQBtn>Continue →</ATTREQBtn></div>
      </div>
    </ATTREQScreen>
  )
}

function ATTREQRegisterLocation() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'8px 28px 32px', height:'calc(100% - 44px)', boxSizing:'border-box', display:'flex', flexDirection:'column' }}>
        <ATTREQStepNav step={2}/>
        <ATTREQML color={C.accent} style={{ display:'block', marginBottom:8 }}>Step 03 — Location</ATTREQML>
        <div style={{ fontFamily:F.display, fontSize:34, fontWeight:600, lineHeight:1.1, color:C.text, marginBottom:6 }}>
          The weather decides<br/><span style={{ fontStyle:'italic', color:C.accent }}>before you do.</span>
        </div>
        <ATTREQBody style={{ marginBottom:20 }}>Share your city for weather-aware suggestions.</ATTREQBody>

        <div style={{ display:'flex', justifyContent:'center', marginBottom:22 }}>
          <div style={{ position:'relative', width:116, height:116, display:'flex', alignItems:'center', justifyContent:'center' }}>
            <div style={{ position:'absolute', width:116, height:116, borderRadius:'50%', border:`1px solid ${C.border}` }}/>
            <div style={{ position:'absolute', width:82, height:82, borderRadius:'50%', border:`1.5px dashed ${C.accentSoft}`, background:C.accentSoft }}/>
            <div style={{ position:'absolute', width:50, height:50, borderRadius:'50%', background:C.text, display:'flex', alignItems:'center', justifyContent:'center' }}>
              <IconLocation size={20} color={C.bg}/>
            </div>
          </div>
        </div>

        <ATTREQCard style={{ padding:'20px' }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, paddingBottom:16, borderBottom:`1px solid ${C.borderSoft}`, marginBottom:18, cursor:'pointer' }}>
            <div style={{ width:36, height:36, borderRadius:100, background:C.accentSoft, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
              <IconLocation size={15} color={C.accent}/>
            </div>
            <div style={{ flex:1 }}>
              <div style={{ fontFamily:F.body, fontSize:14, fontWeight:500, color:C.text }}>Use device location</div>
              <ATTREQML>For weather-aware suggestions</ATTREQML>
            </div>
            <IconChevron size={13} color={C.t3}/>
          </div>
          <ATTREQInput label="Or enter your city" value="New York, London, Tokyo…"/>
        </ATTREQCard>

        <div style={{ marginTop:16 }}>
          <ATTREQBtn style={{ background:C.accent, color:C.bg }}>Create account →</ATTREQBtn>
        </div>
      </div>
    </ATTREQScreen>
  )
}

Object.assign(window, {
  ATTREQStepNav, ATTREQLogin,
  ATTREQRegisterAccount, ATTREQRegisterStyle, ATTREQRegisterLocation,
})
