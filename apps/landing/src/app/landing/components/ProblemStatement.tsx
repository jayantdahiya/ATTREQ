'use client';

import { motion } from 'framer-motion';
import { SectionWrapper } from './SectionWrapper';

export function ProblemStatement() {
  return (
    <SectionWrapper className="landing-section landing-problem">
      <div className="landing-problem__panel">
        <motion.p className="landing-eyebrow" transition={{ delay: 0.02 }}>
          THE PROBLEM
        </motion.p>
        <motion.p className="landing-problem__quote" transition={{ delay: 0.1 }}>
          "The average person spends 17 minutes every morning deciding what to wear."
        </motion.p>
        <motion.p className="landing-problem__body" transition={{ delay: 0.18 }}>
          Decision fatigue starts before your first sip of coffee. A full wardrobe should feel like freedom, but it
          often feels like friction. ATTREQ turns cluttered options into clear recommendations built for your day.
        </motion.p>
      </div>
      <div className="landing-panel">
        <div className="landing-gold-divider" aria-hidden="true" />
      </div>
    </SectionWrapper>
  );
}
