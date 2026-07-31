// ATTREQ Style DNA Onboarding screen

function ATTREQStyleDNA() {
  const { C } = useATTREQTheme(); const F = ATTREQ_F
  const filledGrads = [
    'linear-gradient(155deg,#EDE7DF,#DDD6CC)',
    'linear-gradient(155deg,#DAD4CC,#CAC3BA)',
    'linear-gradient(155deg,#E3DACE,#D5CCBF)',
  ]
  const filledGradsDark = [
    'linear-gradient(155deg,#3C3630,#302A24)',
    'linear-gradient(155deg,#343030,#28242A)',
    'linear-gradient(155deg,#423A2C,#362E22)',
  ]
  const { isDark } = useATTREQTheme()
  const grads = isDark ? filledGradsDark : filledGrads

  return (
    <ATTREQScreen>
      <ATTREQStatusBar/>
      <div style={{ padding:'8px 28px 36px', height:'calc(100% - 44px)', boxSizing:'border-box', display:'flex', flexDirection:'column' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:26 }}>
          <div style={{ width:30, height:30, borderRadius:100, border:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
            <IconBack color={C.t2}/>
          </div>
          <ATTREQML>Style DNA Setup</ATTREQML>
        </div>

        <ATTREQML color={C.accent} style={{ display:'block', marginBottom:8 }}>Step 01 — Upload</ATTREQML>
        <div style={{ fontFamily:F.display, fontSize:34, fontWeight:600, lineHeight:1.1, color:C.text, marginBottom:8 }}>
          Show us<br/><span style={{ fontStyle:'italic', color:C.accent }}>your style.</span>
        </div>
        <ATTREQBody style={{ marginBottom:24 }}>
          Upload 3–8 outfit photos you love. We'll read your aesthetic and pre-fill your wardrobe.
        </ATTREQBody>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:9, marginBottom:16 }}>
          {Array.from({ length:6 }, (_,i) => {
            const filled = i < 3
            return (
              <div key={i} style={{ aspectRatio:'3/4', borderRadius:14, background: filled ? grads[i] : 'transparent', border: filled ? 'none' : `1.5px dashed ${C.border}`, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', overflow:'hidden' }}>
                {!filled && (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.t3} strokeWidth="1.5" strokeLinecap="round">
                    <path d="M12 5v14M5 12h14"/>
                  </svg>
                )}
              </div>
            )
          })}
        </div>

        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:28 }}>
          <div style={{ flex:1, height:3, borderRadius:100, background:C.borderSoft, overflow:'hidden' }}>
            <div style={{ height:'100%', width:'37.5%', background:C.accent, borderRadius:100 }}/>
          </div>
          <ATTREQML>3 of 8 photos</ATTREQML>
        </div>

        <div style={{ marginTop:'auto' }}>
          <ATTREQBtn style={{ background:C.accent, color:C.bg }}>Build my Style DNA →</ATTREQBtn>
          <div style={{ textAlign:'center', marginTop:13 }}>
            <ATTREQML style={{ cursor:'pointer', letterSpacing:'1.2px' }}>Skip for now</ATTREQML>
          </div>
        </div>
      </div>
    </ATTREQScreen>
  )
}

Object.assign(window, { ATTREQStyleDNA })
