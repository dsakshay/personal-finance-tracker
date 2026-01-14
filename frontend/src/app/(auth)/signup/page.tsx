"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api/endpoints";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { isApiError } from "@/lib/api/errors";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.auth.signup({ email, password });
      router.replace("/login");
    } catch (err) {
      if (isApiError(err)) setError(err.message);
      else setError("Signup failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <div className="mb-4">
        <div className="text-lg font-semibold">Sign up</div>
        <div className="text-sm text-neutral-600">Creates an account (then you can login).</div>
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <div className="space-y-1">
          <label className="text-sm font-medium">Email</label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">Password</label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={8}
          />
        </div>

        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>
        ) : null}

        <Button type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create account"}
        </Button>
      </form>

      <div className="mt-4 text-sm text-neutral-700">
        Already have an account?{" "}
        <Link className="underline" href="/login">
          Login
        </Link>
      </div>
    </Card>
  );
}


