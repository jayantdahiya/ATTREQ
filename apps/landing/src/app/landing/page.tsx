import { Features } from './components/Features';
import { FinalCTA } from './components/FinalCTA';
import { Footer } from './components/Footer';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { ProblemStatement } from './components/ProblemStatement';
import { SocialProof } from './components/SocialProof';

export default function LandingPage() {
  return (
    <main className="landing-main">
      <Hero />
      <ProblemStatement />
      <Features />
      <HowItWorks />
      <SocialProof />
      <FinalCTA />
      <Footer />
    </main>
  );
}
