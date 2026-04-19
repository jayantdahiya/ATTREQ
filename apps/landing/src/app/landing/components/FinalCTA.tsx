'use client';

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { appLoginUrl } from '@/lib/urls';
import { SectionWrapper } from './SectionWrapper';

export function FinalCTA() {
  const reduceMotion = useReducedMotion();

  return (
    <SectionWrapper className="landing-section landing-cta-section landing-section--center">
      <div className="landing-gradient-blob landing-gradient-blob--teal landing-gradient-blob--cta-teal" aria-hidden="true" />
      <div className="landing-gradient-blob landing-gradient-blob--gold landing-gradient-blob--cta-gold" aria-hidden="true" />

      <div className="landing-cta-section__content">
        <h2 className="landing-title">Ready to rethink your mornings?</h2>

        <motion.div
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.6 }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.7, delay: 0.1 }}
        >
          <Link href={appLoginUrl} className="landing-cta landing-cta--large" aria-label="Try ATTREQ for free">
            Try ATTREQ - It is Free
          </Link>
        </motion.div>

        <p className="landing-cta-section__note">No credit card required. Your wardrobe stays private.</p>
      </div>
    </SectionWrapper>
  );
}
