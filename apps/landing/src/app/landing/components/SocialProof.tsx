'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { SectionWrapper } from './SectionWrapper';

const personas = [
  'The student rushing between lectures who still wants to look put-together.',
  'The professional who would rather spend their morning on coffee, not closet roulette.',
  'Anyone who has stared at a full wardrobe and thought: I have nothing to wear.',
];

export function SocialProof() {
  const reduceMotion = useReducedMotion();

  return (
    <section className="landing-proof">
      <SectionWrapper className="landing-section landing-section--center">
        <p className="landing-eyebrow">BUILT FOR</p>
        <h2 className="landing-title">People who care about how they look - but not how long it takes.</h2>

        <div className="landing-proof__personas">
          {personas.map((persona, index) => (
            <motion.p
              key={persona}
              className="landing-proof__persona"
              initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 26 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.42 }}
              transition={
                reduceMotion
                  ? { duration: 0 }
                  : {
                      duration: 0.72,
                      delay: 0.08 * index,
                      ease: [0.25, 0.46, 0.45, 0.94],
                    }
              }
            >
              {persona}
            </motion.p>
          ))}
        </div>
      </SectionWrapper>
    </section>
  );
}
