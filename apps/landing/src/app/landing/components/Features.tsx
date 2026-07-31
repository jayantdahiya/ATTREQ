import { SectionWrapper } from './SectionWrapper';

const pieces = [
  { cat: 'Top', color: 'Cream Linen', tone: 'var(--garment-top)' },
  { cat: 'Bottom', color: 'Navy Wool', tone: 'var(--garment-bottom)' },
  { cat: 'Outer', color: 'Camel Coat', tone: 'var(--garment-outer)' },
  { cat: 'Scarf', color: 'Olive Silk', tone: 'var(--garment-accent)' },
  { cat: 'Top', color: 'White Cotton', tone: 'var(--garment-top)' },
  { cat: 'Shoes', color: 'Charcoal Tweed', tone: 'var(--garment-shoes)' },
];

const notes = [
  {
    tag: 'Weather-aware',
    tagClass: 'landing-note__tag--moss',
    title: 'Dressed for the forecast',
    body: 'Looks are matched to the temperature and sky outside your door — linen on the warm days, wool when it turns.',
  },
  {
    tag: 'Style DNA',
    tagClass: 'landing-note__tag--bronze',
    title: 'Your taste, distilled',
    body: 'Every wear and skip refines what ATTREQ knows about you. The looks get more yours each week.',
  },
  {
    tag: 'Private',
    tagClass: 'landing-note__tag--clay',
    title: 'Your closet stays yours',
    body: 'Your wardrobe photos power your recommendations and nothing else. No feeds, no followers, no resale prompts.',
  },
];

export function Features() {
  return (
    <SectionWrapper className="landing-section">
      <div className="landing-wardrobe__head">
        <p className="landing-ml landing-ml--bronze">The wardrobe</p>
        <h2 className="landing-title">
          Every piece, <span className="landing-em">catalogued.</span>
        </h2>
        <p className="landing-body">
          Your closet becomes a browsable archive — each garment tagged by
          category, color, and season the moment you photograph it.
        </p>
      </div>

      <div className="landing-wardrobe__strip">
        {pieces.map((piece) => (
          <div key={piece.color} className="landing-wardrobe__piece">
            <div className="landing-wardrobe__swatch" style={{ background: piece.tone }} aria-hidden="true" />
            <div className="landing-wardrobe__caption">
              <span className="landing-wardrobe__cat">{piece.cat}</span>
              <span className="landing-ml">{piece.color}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="landing-notes">
        {notes.map((note) => (
          <div key={note.tag} className="landing-note">
            <span className={`landing-note__tag ${note.tagClass}`}>{note.tag}</span>
            <h3 className="landing-note__title">{note.title}</h3>
            <p className="landing-note__body">{note.body}</p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  );
}
