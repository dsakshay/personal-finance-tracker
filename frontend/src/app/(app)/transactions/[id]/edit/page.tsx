"use client";

import { useMemo, useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import type { Account } from "@/lib/api/types";
import { isApiError } from "@/lib/api/errors";

export default function EditTransactionPage() {
  const router = useRouter();
  const params = useParams();
  const qc = useQueryClient();

  const transactionId = params.id as string;

  const [accountId, setAccountId] = useState("");
  const [amount, setAmount] = useState("0.00");
  const [currency, setCurrency] = useState("INR");
  const [tag, setTag] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [description, setDescription] = useState("");
  const [transactionDate, setTransactionDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Fetch transaction details
  const txnQuery = useQuery({
    queryKey: queryKeys.transactions.detail(transactionId),
    queryFn: () => api.transactions.get(transactionId),
    enabled: !!transactionId,
  });

  // Fetch accounts
  const accountsQuery = useQuery({
    queryKey: queryKeys.accounts.list({}),
    queryFn: () => api.accounts.list(),
  });

  const accounts: Account[] = accountsQuery.data?.accounts ?? [];
  const transaction = txnQuery.data;

  // Pre-fill form when transaction loads
  useEffect(() => {
    if (transaction && !initialized) {
      // Check if it's a transfer
      if (transaction.transaction_type === "transfer") {
        setError("Cannot edit transfers. Delete and recreate if needed.");
        return;
      }

      // Convert amount to positive for form (amount_minor / 100, then abs)
      const amountValue = Math.abs(parseFloat(transaction.amount));
      setAmount(amountValue.toFixed(2));

      setAccountId(transaction.account_id);
      setCurrency(transaction.currency);
      setTag(transaction.tag);
      setPaymentMethod(transaction.payment_method || "");
      setDescription(transaction.description || "");
      setTransactionDate(transaction.transaction_date);
      setInitialized(true);
    }
  }, [transaction, initialized]);

  const inferredCurrency = useMemo(() => {
    const a = accounts.find((x) => x.id === accountId);
    return a?.currency ?? currency;
  }, [accounts, accountId, currency]);

  const updateTxn = useMutation({
    mutationFn: async () => {
      setError(null);
      return api.transactions.update(transactionId, {
        account_id: accountId,
        amount,
        tag: tag || undefined,
        payment_method: paymentMethod || undefined,
        description: description || undefined,
        transaction_date: transactionDate,
      });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: queryKeys.transactions.list({}) });
      await qc.invalidateQueries({ queryKey: queryKeys.transactions.detail(transactionId) });
      await qc.invalidateQueries({ queryKey: queryKeys.accounts.list({}) });
      router.replace("/transactions");
    },
    onError: (err) => {
      if (isApiError(err)) setError(err.message);
      else setError("Failed to update transaction");
    },
  });

  if (txnQuery.isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-lg font-semibold">Loading...</div>
      </div>
    );
  }

  if (txnQuery.isError || !transaction) {
    return (
      <div className="space-y-4">
        <div className="text-lg font-semibold">Transaction not found</div>
        <Button onClick={() => router.back()}>Go back</Button>
      </div>
    );
  }

  if (transaction.transaction_type === "transfer") {
    return (
      <div className="space-y-4">
        <div className="text-lg font-semibold">Cannot edit transfer</div>
        <div className="text-sm text-neutral-800">
          Transfers cannot be edited. Delete and recreate if needed.
        </div>
        <Button onClick={() => router.back()}>Go back</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="text-lg font-semibold">Edit transaction</div>
        <div className="text-sm text-neutral-800">
          Editing {transaction.transaction_type}: {transaction.tag}
        </div>
      </div>

      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Type</div>
            <select
              className="w-full rounded-md border border-neutral-300 bg-gray-100 px-3 py-2 text-sm"
              value={transaction.transaction_type}
              disabled
            >
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
            <div className="text-xs text-neutral-500">Cannot change type</div>
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Date</div>
            <Input
              type="date"
              value={transactionDate}
              onChange={(e) => setTransactionDate(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Amount</div>
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
            <div className="text-xs font-medium text-neutral-800">Account</div>
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

          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Tag</div>
            <Input value={tag} onChange={(e) => setTag(e.target.value)} placeholder="groceries" required />
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Payment method (optional)</div>
            <Input value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} placeholder="card/upi" />
          </div>
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Currency</div>
            <Input value={inferredCurrency} disabled />
          </div>
        </div>

        <div className="mt-4 space-y-1">
          <div className="text-xs font-medium text-neutral-800">Description (optional)</div>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Notes…" />
        </div>

        {error ? (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>
        ) : null}

        <div className="mt-4 flex gap-2">
          <Button
            disabled={updateTxn.isPending}
            onClick={() => {
              updateTxn.mutate();
            }}
          >
            {updateTxn.isPending ? "Updating..." : "Update"}
          </Button>
          <Button variant="secondary" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </Card>
    </div>
  );
}
