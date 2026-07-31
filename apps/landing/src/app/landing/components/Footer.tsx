export function Footer() {
  const copy = String.fromCharCode(169);

  return (
    <footer className="landing-footer">
      <div className="landing-footer__inner">
        <div>
          <p className="landing-footer__wordmark">ATTREQ</p>
          <p className="landing-footer__tagline">Your closet, curated.</p>
        </div>
        <p className="landing-footer__copy">{copy} 2026 ATTREQ. All rights reserved.</p>
      </div>
    </footer>
  );
}
