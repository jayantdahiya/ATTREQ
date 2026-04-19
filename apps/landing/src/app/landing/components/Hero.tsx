'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { appLoginUrl } from '@/lib/urls';

export function Hero() {
  const reduceMotion = useReducedMotion();

  const transition = reduceMotion
    ? { duration: 0 }
    : { duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number] };

  return (
    <header className="landing-hero">
      <div className="landing-topbar">
        <motion.p
          className="landing-wordmark"
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition}
        >
          ATTREQ
        </motion.p>
        <motion.div
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduceMotion ? { duration: 0 } : { ...transition, delay: 0.1 }}
        >
          <Link href={appLoginUrl} className="landing-topbar__link">
            Try ATTREQ <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </motion.div>
      </div>

      <div className="landing-hero__ambient" aria-hidden="true">
        <div className="landing-gradient-blob landing-gradient-blob--teal landing-gradient-blob--hero-teal" />
        <div className="landing-gradient-blob landing-gradient-blob--gold landing-gradient-blob--hero-gold" />
      </div>

      <div className="landing-hero__content">
        <motion.h1
          className="landing-display"
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduceMotion ? { duration: 0 } : { ...transition, delay: 0.18 }}
        >
          Your closet, curated.
        </motion.h1>

        <motion.p
          className="landing-subtitle landing-hero__subtext"
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduceMotion ? { duration: 0 } : { ...transition, delay: 0.28 }}
        >
          AI-powered outfit suggestions that learn your style, so your mornings do not have to be a struggle.
        </motion.p>

        <motion.div
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduceMotion ? { duration: 0 } : { ...transition, delay: 0.36 }}
        >
          <Link href={appLoginUrl} className="landing-cta" aria-label="Get started with ATTREQ">
            Get Started
          </Link>
        </motion.div>
      </div>
    </header>
  );
}
