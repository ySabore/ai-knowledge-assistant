import { SignIn, SignedIn, UserButton } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export default function SignInPage() {
  if (!clerkPublishableKey) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="auth-kicker">Clerk Setup Required</p>
          <h1>Sign in with Clerk</h1>
          <p className="auth-copy">
            Add <code>VITE_CLERK_PUBLISHABLE_KEY</code> to your web environment, then enable
            email and GitHub sign-in in your Clerk dashboard.
          </p>
          <div className="auth-note">
            Clerk is not initialized yet, so the hosted sign-in form cannot render.
          </div>
          <div className="auth-note">
            <strong>TODO:</strong> Enterprise Login Center stays on the roadmap as an optional UX
            layer over Clerk.
          </div>
          <Link to="/" className="auth-link">
            Back to landing page
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="auth-kicker">Clerk Authentication</p>
        <h1>Sign in with Clerk</h1>
        <p className="auth-copy">
          Sign in with your work email or your GitHub account. Clerk will handle the hosted
          authentication flow and return you to the AI Knowledge Assistant app.
        </p>
        <div className="auth-note">
          <strong>TODO:</strong> Enterprise Login Center remains an optional future wrapper for
          enterprise-focused sign-in flows.
        </div>
        <SignedIn>
          <div className="auth-note auth-signed-in">
            You are already signed in.
            <span className="auth-user-button">
              <UserButton afterSignOutUrl="/" />
            </span>
          </div>
          <Link to="/app" className="auth-link auth-link-primary">
            Open app
          </Link>
        </SignedIn>
        <div className="clerk-panel">
          <SignIn routing="path" path="/sign-in" fallbackRedirectUrl="/app" />
        </div>
        <Link to="/" className="auth-link">
          Back to landing page
        </Link>
      </section>
    </main>
  );
}
