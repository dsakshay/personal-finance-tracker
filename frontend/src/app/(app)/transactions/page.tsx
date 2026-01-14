"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { formatMoney } from "@/lib/money/money";
import type { TransactionType } from "@/lib/api/types";

export default function TransactionsPage() {
  const [accountId, setAccountId] = useState("");
  const [tag, setTag] = useState("");
  const [type, setType] = useState<TransactionType | "">("");

  const params = useMemo(
    () => ({
      account_id: accountId || undefined,
      tag: tag || undefined,
      transaction_type: type || undefined,
      limit: 100,
      offset: 0,
    }),
    [accountId, tag, type]
  );

  const q = useQuery({
    queryKey: queryKeys.transactions.list(params),
    queryFn: () => api.transactions.list(params),
  });

  const accountsQ = useQuery({
    queryKey: queryKeys.accounts.list({}),
    queryFn: () => api.accounts.list(),
  });

  const clearFilters = () => {
    setAccountId("");
    setTag("");
    setType("");
  };

  const hasActiveFilters = accountId || tag || type;

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-lg font-semibold">Transactions</div>
          <div className="text-sm text-neutral-800">Income, expenses, and transfers.</div>
        </div>
        <Link
          href="/transactions/new"
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800"
        >
          New transaction
        </Link>
      </div>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold">Filters</div>
          {hasActiveFilters && (
            <Button variant="secondary" onClick={clearFilters}>
              Clear filters
            </Button>
          )}
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Account</div>
            <select
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
            >
              <option value="">All accounts</option>
              {accountsQ.data?.accounts.map((acc) => (
                <option key={acc.id} value={acc.id}>
                  {acc.name} ({acc.currency})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Type</div>
            <select
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
              value={type}
              onChange={(e) => setType(e.target.value as any)}
            >
              <option value="">All types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs font-medium text-neutral-800">Tag</div>
            <Input value={tag} onChange={(e) => setTag(e.target.value)} placeholder="Search by tag..." />
          </div>
        </div>
      </Card>

      <Card>
        {q.isLoading ? (
          <div className="text-sm text-neutral-800">Loading transactions…</div>
        ) : q.isError ? (
          <div className="text-sm text-red-700">Failed to load transactions.</div>
        ) : q.data.transactions.length === 0 ? (
          <div className="text-sm text-neutral-800">No transactions found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-neutral-500">
                <tr>
                  <th className="py-2 pr-3">Date</th>
                  <th className="py-2 pr-3">Account</th>
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Tag</th>
                  <th className="py-2 pr-3">Description</th>
                  <th className="py-2 pr-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {q.data.transactions.map((t) => (
                  <tr key={t.id} className="border-t border-neutral-200">
                    <td className="py-2 pr-3 text-neutral-900">{t.transaction_date}</td>
                    <td className="py-2 pr-3 text-neutral-900">
                      <div className="font-medium">{t.account_name}</div>
                      {t.related_account_name ? (
                        <div className="text-xs text-neutral-500">
                          related: {t.related_account_name}
                        </div>
                      ) : null}
                    </td>
                    <td className="py-2 pr-3 text-neutral-900">{t.transaction_type}</td>
                    <td className="py-2 pr-3 text-neutral-900">{t.tag}</td>
                    <td className="py-2 pr-3 text-neutral-900">{t.description ?? ""}</td>
                    <td className="py-2 pr-3 text-right font-medium text-neutral-900">
                      {formatMoney(t.amount, { currency: t.currency })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}


