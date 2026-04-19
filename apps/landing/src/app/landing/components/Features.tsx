'use client';

import { Aperture, Compass, BrainCircuit } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { SectionWrapper } from './SectionWrapper';

const featureCards = [
  {
    key: 'capture',
    label: '01 - CAPTURE',
    title: 'Snap. Upload. Done.',
    body: 'Photograph your wardrobe and let AI handle the rest - detecting colors, categories, seasons, and occasions automatically.',
    icon: Aperture,
  },
  {
    key: 'discover',
    label: '02 - DISCOVER',
    title: 'Your daily outfit, decided.',
    body: 'Every morning, get a curated set of outfit suggestions based on weather, your calendar, and what you have not worn lately.',
    icon: Compass,
  },
  {
    key: 'evolve',
    label: '03 - EVOLVE',
    title: 'It learns. You wear.',
    body: 'Rate what you wear, dismiss what you do not. Every interaction makes your AI stylist sharper.',
    icon: BrainCircuit,
  },
];

export function Features() {
  const reduceMotion = useReducedMotion();

  return (
    <SectionWrapper className="landing-section landing-features">
      <p className="landing-eyebrow">THE PILLARS</p>
      <h2 className="landing-title">Three moves. One smarter wardrobe loop.</h2>

      <div className="landing-features__grid">
        {featureCards.map((feature, index) => {
          const Icon = feature.icon;

          return (
            <motion.article
              key={feature.key}
              className="landing-features__card"
              initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 46 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={
                reduceMotion
                  ? { duration: 0 }
                  : {
                      duration: 0.84,
                      delay: 0.12 * index,
                      ease: [0.25, 0.46, 0.45, 0.94],
                    }
              }
            >
              <div className="landing-features__icon">
                <Icon size={20} aria-hidden="true" />
              </div>
              <p className="landing-label">{feature.label}</p>
              <h3 className="landing-features__headline">{feature.title}</h3>
              <p className="landing-features__body">{feature.body}</p>
            </motion.article>
          );
        })}
      </div>
    </SectionWrapper>
  );
}
