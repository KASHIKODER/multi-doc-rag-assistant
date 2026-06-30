import Link from "next/link";
import { GitHubLoginButton } from "@/components/auth/GitHubLoginButton";
import { APP_CONFIG, APP_ROUTES } from "@/lib/constants";

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl items-center justify-center px-6 py-10">
        <div className="grid w-full gap-8 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="flex flex-col justify-center">
            <Link
              href={APP_ROUTES.landing}
              className="text-sm font-semibold text-[#2563EB]"
            >
              {APP_CONFIG.name}
            </Link>

            <h1 className="mt-5 max-w-xl text-5xl font-semibold leading-tight tracking-tight">
              Sign in to your document intelligence workspace.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">
              Access your documents, ask source-grounded questions, review
              verified answers, and continue previous sessions from one clean
              workspace.
            </p>

            <div className="mt-8 grid max-w-md gap-3">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-sm font-semibold text-[#0F172A]">
                  Source-first answers
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Answers are designed around citations, retrieved context, and
                  verified claims.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-sm font-semibold text-[#0F172A]">
                  GitHub authentication
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Sign in with GitHub to prepare this workspace for protected
                  dashboards, saved answers, and future user history.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <div>
              <p className="text-sm font-semibold text-[#2563EB]">
                Welcome back
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Continue to DocuMind
              </h2>

              <p className="mt-3 text-sm leading-6 text-slate-600">
                Use GitHub sign-in to access the product workspace. Route
                protection and persistent user history will be added in later
                product stages.
              </p>
            </div>

            <div className="mt-8 grid gap-3">
              <GitHubLoginButton />

              <Link
                href={APP_ROUTES.dashboard}
                className="flex w-full items-center justify-center rounded-2xl bg-[#2563EB] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
              >
                Continue in Demo Mode
              </Link>
            </div>

            <div className="mt-6 rounded-2xl bg-[#10B981]/10 p-4">
              <p className="text-sm font-semibold text-[#0F172A]">
                Local development mode
              </p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                GitHub login is active for local development. Demo mode remains
                available while protected routes are being prepared.
              </p>
            </div>

            <p className="mt-6 text-center text-sm text-slate-500">
              Need to inspect the system first?{" "}
              <Link
                href={APP_ROUTES.developer}
                className="font-semibold text-[#2563EB]"
              >
                View pipeline
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}