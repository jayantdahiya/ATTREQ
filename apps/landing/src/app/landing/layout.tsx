export default function LandingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="landing-root" data-landing="true">
      {children}
    </div>
  );
}
