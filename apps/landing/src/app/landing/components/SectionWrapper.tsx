'use client';

import { useRef } from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';

type SectionWrapperProps = {
  className?: string;
  children: React.ReactNode;
};

export function SectionWrapper({ className, children }: SectionWrapperProps) {
  const ref = useRef<HTMLElement | null>(null);
  const isInView = useInView(ref, { once: true, margin: '-120px 0px' });
  const reduceMotion = useReducedMotion();

  return (
    <section ref={ref} className={className}>
      <motion.div
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 36 }}
        animate={
          isInView
            ? { opacity: 1, y: 0 }
            : reduceMotion
              ? { opacity: 1, y: 0 }
              : {}
        }
        transition={reduceMotion ? { duration: 0 } : { duration: 0.82, ease: [0.25, 0.46, 0.45, 0.94] }}
      >
        {children}
      </motion.div>
    </section>
  );
}
