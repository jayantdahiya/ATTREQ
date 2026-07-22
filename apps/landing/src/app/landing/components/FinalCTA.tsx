import Link from 'next/link';
import { appLoginUrl } from '@/lib/urls';
import { SectionWrapper } from './SectionWrapper';

export function FinalCTA() {
  return (
    <div className="landing-coda">
      <SectionWrapper className="landing-coda__inner">
        <p className="landing-coda__ml">After dark</p>
        <h2 className="landing-coda__title">
          Tomorrow&rsquo;s look is <em>already decided.</em>
        </h2>
        <p className="landing-coda__body">
          Photograph your closet tonight and wake up to your first three looks.
          Light mode, dark mode — ATTREQ dresses well in both.
        </p>
        <Link href={appLoginUrl} className="landing-coda__cta">
          Get started
        </Link>
        <p className="landing-coda__note">Free while in beta — your photos stay private</p>
      </SectionWrapper>
    </div>
  );
}
