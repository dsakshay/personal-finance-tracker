"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import type { Account, TransactionType } from "@/lib/api/types";
import { isApiError } from "@/lib/api/errors";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

type Mode = "income" | "expense" | "transfer";

export default function NewTransactionPage() {
  const router = useRouter();
  const qc = useQueryClient();

  const [mode, setMode] = useState<Mode>("expense");
  const [accountId, setAccountId] = useState("");
  const [relatedAccountId, setRelatedAccountId] = useState("");
  const [amount, setAmount] = useState("0.00");
  const [currency, setCurrency] = useState("INR");
  const [tag, setTag] = useState("groceries");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [description, setDescription] = useState("");
  const [transactionDate, setTransactionDate] = useState(todayISO());
  const [error, setError] = useState<string | null>(null);

  const accountsQuery = useQuery({
    queryKey: queryKeys.accounts.list({}),
    queryFn: () => api.accounts.list(),
  });

  const accounts: Account[] = accountsQuery.data?.accounts ?? [];

  const inferredCurrency = useMemo(() => {
    const a = accounts.find((x) => x.id === accountId);
    return a?.currency ?? currency;
  }, [accounts, accountId, currency]);

  const createTxn = useMutation({
    mutationFn: async () => {
      setError(null);
      if (mode === "transfer") {
        return api.transactions.transfer({
          account_id: accountId,
          related_account_id: relatedAccountId,
          amount,
          currency: inferredCurrency,
          payment_method: paymentMethod || undefined,
          description: description || undefined,
          transaction_date: transactionDate,
        });
      }
      const transaction_type: Exclude<TransactionType, "transfer"> = mode;
      return api.transactions.create({
        account_id: accountId,
        amount,
        currency: inferredCurrency,
        transaction_type,
        tag: tag || (mode === "income" ? "income" : "expense"),
        payment_method: paymentMethod || undefined,
        description: description || undefined,
        transaction_date: transactionDate,
      });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: queryKeys.transactions.list({}) });
      await qc.invalidateQueries({ queryKey: queryKeys.accounts.list({}) });
      router.replace("/transactions");
    },
    onError: (err) => {
      if (isApiError(err)) setError(err.message);
      else setError("Failed to create transaction");
    },
  });

  return (
    <div className="space-y-4">
      <div>
        <div className="text-lg font-semibold">New transaction</div>
        <div className="text-sm text-neutral-600">
          Amount must be positive; backend applies sign (expense becomes negative).
        </div>
      </div>

      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">Type</div>
            <select
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              value={mode}
              onChange={(e) => {
                const next = e.target.value as Mode;
                setMode(next);
                setError(null);
                setTag(next === "transfer" ? "transfer" : next === "income" ? "salary" : "groceries");
              }}
            >
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">Date</div>
            <Input
              type="date"
              value={transactionDate}
              onChange={(e) => setTransactionDate(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">Amount</div>
            <Input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="500.00"
              inputMode="decimal"
              pattern="^\\d+\\.\\d{2}$"
              required
            />
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">{mode === "transfer" ? "From account" : "Account"}</div>
            <select
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.currency})
                </option>
              ))}
            </select>
          </div>

          {mode === "transfer" ? (
            <div className="space-y-1">
              <div className="text-xs font-medium text-neutral-600">To account</div>
              <select
                className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
                value={relatedAccountId}
                onChange={(e) => setRelatedAccountId(e.target.value)}
                required
              >
                <option value="" disabled>
                  Select…
                </option>
                {accounts
                  .filter((a) => a.id !== accountId)
                  .map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} ({a.currency})
                    </option>
                  ))}
              </select>
            </div>
          ) : (
            <div className="space-y-1">
              <div className="text-xs font-medium text-neutral-600">Tag</div>
              <Input value={tag} onChange={(e) => setTag(e.target.value)} placeholder="groceries" required />
            </div>
          )}
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">Payment method (optional)</div>
            <Input value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} placeholder="card/upi" />
          </div>
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-600">Currency</div>
            <Input value={inferredCurrency} disabled />
          </div>
        </div>

        <div className="mt-4 space-y-1">
          <div className="text-xs font-medium text-neutral-600">Description (optional)</div>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Notes…" />
        </div>

        {error ? (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>
        ) : null}

        <div className="mt-4 flex gap-2">
          <Button
            disabled={createTxn.isPending}
            onClick={() => {
              createTxn.mutate();
            }}
          >
            {createTxn.isPending ? "Creating..." : "Create"}
          </Button>
          <Button variant="secondary" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </Card>
    </div>
  );
}


