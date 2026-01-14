"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api/endpoints";
import { setAuthToken } from "@/lib/auth/token";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { isApiError } from "@/lib/api/errors";

export default function LoginPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.auth.login({ email, password });
      setAuthToken(res.access_token);
      router.replace(next);
    } catch (err) {
      if (isApiError(err)) setError(err.message);
      else setError("Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <div className="mb-4">
        <div className="text-lg font-semibold">Login</div>
        <div className="text-sm text-neutral-800">Use your email/password to get a JWT token.</div>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <div className="space-y-1">
          <label className="text-sm font-medium text-neutral-900">Email</label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-neutral-900">Password</label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>
        ) : null}

        <Button type="submit" disabled={submitting}>
          {submitting ? "Logging in..." : "Login"}
        </Button>
      </form>

      <div className="mt-4 text-sm text-neutral-900">
        No account?{" "}
        <Link className="underline font-medium" href="/signup">
          Sign up
        </Link>
      </div>
    </Card>
  );
}


