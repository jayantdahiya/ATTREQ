import { SectionWrapper } from './SectionWrapper';

const steps = [
  {
    no: 'No. 01',
    title: 'Photograph your closet',
    body: 'Point your camera at each piece, or pick from your photo library. ATTREQ recognizes the garment, its color, and its category, and files it into your digital wardrobe.',
  },
  {
    no: 'No. 02',
    title: 'Teach it your taste',
    body: 'Upload a handful of outfits you love — yours or anyone’s. ATTREQ distills them into your Style DNA: the silhouettes, palettes, and moods you actually reach for.',
  },
  {
    no: 'No. 03',
    title: 'Get dressed',
    body: 'Each morning you get three looks composed from your own clothes and matched to the day’s weather. Wear one or skip it — every choice sharpens tomorrow’s looks.',
  },
];

export function HowItWorks() {
  return (
    <SectionWrapper className="landing-section" id="how-it-works">
      <div className="landing-works__intro">
        <p className="landing-ml landing-ml--bronze">How it works</p>
        <h2 className="landing-title">
          Three steps, then it&rsquo;s <span className="landing-em">effortless.</span>
        </h2>
      </div>

      <div className="landing-works__docket">
        {steps.map((step) => (
          <div key={step.no} className="landing-works__step">
            <span className="landing-works__no">{step.no}</span>
            <h3 className="landing-works__step-title">{step.title}</h3>
            <p className="landing-works__step-body">{step.body}</p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  );
}
