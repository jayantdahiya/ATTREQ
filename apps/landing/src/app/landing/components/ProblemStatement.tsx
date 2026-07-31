import { SectionWrapper } from './SectionWrapper';

export function ProblemStatement() {
  return (
    <SectionWrapper className="landing-section">
      <div className="landing-problem__panel">
        <p className="landing-ml">The morning problem</p>
        <blockquote className="landing-problem__quote">
          A full closet and nothing to wear isn&rsquo;t a wardrobe problem.
          It&rsquo;s a <span className="landing-em">decision</span> problem.
        </blockquote>
        <p className="landing-body landing-problem__body">
          Most of us wear a fifth of what we own and stand in front of the rest
          every morning. ATTREQ makes the decision for you — from your own
          clothes, in your own taste, before you&rsquo;ve finished your coffee.
        </p>
      </div>
    </SectionWrapper>
  );
}
