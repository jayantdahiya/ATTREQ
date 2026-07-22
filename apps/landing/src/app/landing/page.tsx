import { Features } from './components/Features';
import { FinalCTA } from './components/FinalCTA';
import { Footer } from './components/Footer';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { ProblemStatement } from './components/ProblemStatement';

export default function LandingPage() {
  return (
    <main className="landing-main">
      <Hero />
      <ProblemStatement />
      <HowItWorks />
      <Features />
      <FinalCTA />
      <Footer />
    </main>
  );
}
