'use client';

import { motion, useInView, useReducedMotion } from 'framer-motion';
import { useRef } from 'react';

const steps = [
  {
    title: 'Photograph your clothes',
    body: 'Open the app, point your camera, and capture each piece. AI identifies what it is instantly.',
  },
  {
    title: 'Get daily suggestions',
    body: 'Every morning, open ATTREQ for a fresh set of outfits tailored to your day.',
  },
  {
    title: 'Wear and rate',
    body: 'Put it on. Loved it? Tell us. Not feeling it? Skip and the system adapts.',
  },
  {
    title: 'Watch it get smarter',
    body: 'Your feedback loop compounds. Each day, recommendations become a better fit.',
  },
];

export function HowItWorks() {
  const ref = useRef<HTMLElement | null>(null);
  const isInView = useInView(ref, { once: true, margin: '-120px 0px' });
  const reduceMotion = useReducedMotion();

  return (
    <section ref={ref} className="landing-section landing-works">
      <motion.div
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 36 }}
        animate={isInView ? { opacity: 1, y: 0 } : reduceMotion ? { opacity: 1, y: 0 } : {}}
        transition={reduceMotion ? { duration: 0 } : { duration: 0.84, ease: [0.25, 0.46, 0.45, 0.94] }}
      >
        <p className="landing-eyebrow">HOW IT WORKS</p>
        <h2 className="landing-title">A ritual built for mornings that move fast.</h2>

        <div className="landing-works__timeline">
          <motion.div
            className="landing-works__line"
            initial={reduceMotion ? { scaleY: 1 } : { scaleY: 0 }}
            animate={isInView ? { scaleY: 1 } : reduceMotion ? { scaleY: 1 } : { scaleY: 0 }}
            transition={reduceMotion ? { duration: 0 } : { duration: 1.1, delay: 0.12 }}
            aria-hidden="true"
          />

          {steps.map((step, index) => (
            <motion.article
              key={step.title}
              className="landing-works__step"
              initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 34 }}
              animate={
                isInView
                  ? { opacity: 1, y: 0 }
                  : reduceMotion
                    ? { opacity: 1, y: 0 }
                    : {}
              }
              transition={
                reduceMotion
                  ? { duration: 0 }
                  : {
                      duration: 0.78,
                      delay: 0.16 + index * 0.1,
                      ease: [0.25, 0.46, 0.45, 0.94],
                    }
              }
            >
              <div className="landing-works__number">{index + 1}</div>
              <div className="landing-works__step-card">
                <h3 className="landing-works__step-title">{step.title}</h3>
                <p className="landing-works__step-body">{step.body}</p>
              </div>
            </motion.article>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
