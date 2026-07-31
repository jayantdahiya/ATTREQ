'use client';

import Link from 'next/link';
import { ArrowRight, ArrowDown } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { appLoginUrl } from '@/lib/urls';
import { PhoneMock } from './PhoneMock';

export function Hero() {
  const reduceMotion = useReducedMotion();

  const rise = (delay: number) => ({
    initial: reduceMotion ? { opacity: 1 } : { opacity: 0, y: 22 },
    animate: { opacity: 1, y: 0 },
    transition: reduceMotion
      ? { duration: 0 }
      : { duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] as const, delay },
  });

  return (
    <header className="landing-hero">
      <div className="landing-topbar">
        <motion.p className="landing-wordmark" {...rise(0)}>
          ATTREQ
        </motion.p>
        <motion.div {...rise(0.08)}>
          <Link href={appLoginUrl} className="landing-ghost-link">
            Open the app <ArrowRight size={13} aria-hidden="true" />
          </Link>
        </motion.div>
      </div>

      <div className="landing-hero__copy">
        <motion.p className="landing-ml landing-ml--bronze" {...rise(0.14)}>
          Your closet, curated
        </motion.p>

        <motion.h1 className="landing-display" {...rise(0.22)}>
          Your best outfit is <span className="landing-em">already hanging</span> in your closet.
        </motion.h1>

        <motion.p className="landing-body landing-hero__sub" {...rise(0.3)}>
          ATTREQ learns your taste from the outfits you love, checks the morning&rsquo;s
          weather, and lays out looks made only from clothes you own. No shopping,
          no stylists — just your wardrobe, finally working for you.
        </motion.p>

        <motion.div className="landing-hero__actions" {...rise(0.38)}>
          <Link href={appLoginUrl} className="landing-cta">
            Get started
          </Link>
          <a href="#how-it-works" className="landing-ghost-link">
            How it works <ArrowDown size={13} aria-hidden="true" />
          </a>
        </motion.div>
      </div>

      <motion.div
        className="landing-hero__stage"
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 36 }}
        animate={{ opacity: 1, y: 0 }}
        transition={
          reduceMotion
            ? { duration: 0 }
            : { duration: 1, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.3 }
        }
      >
        <div className="landing-hero__swatch landing-hero__swatch--a" aria-hidden="true" />
        <div className="landing-hero__swatch landing-hero__swatch--b" aria-hidden="true" />
        <PhoneMock />
      </motion.div>
    </header>
  );
}
