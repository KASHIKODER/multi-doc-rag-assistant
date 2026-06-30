"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/Button";

function getCallbackUrl() {
  if (typeof window === "undefined") {
    return "/dashboard";
  }

  const params = new URLSearchParams(window.location.search);
  return params.get("callbackUrl") || "/dashboard";
}

export function GitHubLoginButton() {
  const [loading, setLoading] = useState(false);

  async function handleGitHubLogin() {
    setLoading(true);

    await signIn("github", {
      callbackUrl: getCallbackUrl(),
    });
  }

  return (
    <Button
      type="button"
      variant="secondary"
      size="lg"
      fullWidth
      disabled={loading}
      onClick={handleGitHubLogin}
    >
      {loading ? "Redirecting to GitHub..." : "Continue with GitHub"}
    </Button>
  );
}