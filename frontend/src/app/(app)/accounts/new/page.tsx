"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import type { CurrencyCode } from "@/lib/api/types";
import { isApiError } from "@/lib/api/errors";

const currencies: CurrencyCode[] = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SGD"];

export default function NewAccountPage() {
  const router = useRouter();
  const qc = useQueryClient();

  const [name, setName] = useState("");
  const [currency, setCurrency] = useState<CurrencyCode>("INR");
  const [openingBalance, setOpeningBalance] = useState("0.00");
  const [error, setError] = useState<string | null>(null);

  const m = useMutation({
    mutationFn: () =>
      api.accounts.create({
        name,
        currency,
        opening_balance: openingBalance,
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: queryKeys.accounts.list({}) });
      router.replace("/accounts");
    },
    onError: (err) => {
      if (isApiError(err)) setError(err.message);
      else setError("Failed to create account");
    },
  });

  return (
    <div className="space-y-4">
      <div>
        <div className="text-lg font-semibold">New account</div>
        <div className="text-sm text-neutral-600">Currency is immutable in the MVP.</div>
      </div>

      <Card>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            m.mutate();
          }}
        >
          <div className="space-y-1">
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Currency</label>
            <select
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
            >
              {currencies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Opening balance</label>
            <Input
              value={openingBalance}
              onChange={(e) => setOpeningBalance(e.target.value)}
              placeholder="0.00"
              inputMode="decimal"
              pattern="^-?\\d+\\.\\d{2}$"
            />
            <div className="text-xs text-neutral-500">Must be a decimal string with 2 places (e.g. 1000.00).</div>
          </div>

          {error ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>
          ) : null}

          <div className="flex gap-2">
            <Button type="submit" disabled={m.isPending}>
              {m.isPending ? "Creating..." : "Create"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}


