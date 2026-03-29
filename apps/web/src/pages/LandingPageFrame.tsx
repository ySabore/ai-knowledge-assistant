import landingPageHtml from "../../../../docs/architecture/landing-page.html?raw";

export default function LandingPageFrame() {
  return (
    <iframe
      title="AI Knowledge Assistant Landing Page"
      srcDoc={landingPageHtml}
      className="block h-full w-full border-0"
    />
  );
}
