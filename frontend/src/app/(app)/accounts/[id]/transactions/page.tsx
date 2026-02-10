"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { formatMoney } from "@/lib/money/money";
import type { TransactionType } from "@/lib/api/types";

export default function AccountTransactionsPage() {
  const params = useParams();
  const accountId = params.id as string;

  const [tag, setTag] = useState("");
  const [type, setType] = useState<TransactionType | "">("");

  // Fetch account details
  const accountsQuery = useQuery({
    queryKey: queryKeys.accounts.list({}),
    queryFn: () => api.accounts.list(),
  });

  const account = accountsQuery.data?.accounts.find((a) => a.id === accountId);

  // Fetch transactions for this account
  const transactionsQuery = useQuery({
    queryKey: queryKeys.transactions.list({
      account_id: accountId,
      tag: tag || undefined,
      transaction_type: type || undefined,
      limit: 100,
      offset: 0,
    }),
    queryFn: () =>
      api.transactions.list({
        account_id: accountId,
        tag: tag || undefined,
        transaction_type: type || undefined,
        limit: 100,
        offset: 0,
      }),
    enabled: !!accountId,
  });

  const clearFilters = () => {
    setTag("");
    setType("");
  };

  const hasActiveFilters = tag || type;

  if (accountsQuery.isLoading) {
    return (
      <div className="space-y-4">
        <div className="text-lg font-semibold">Loading...</div>
      </div>
    );
  }

  if (!account) {
    return (
      <div className="space-y-4">
        <div className="text-lg font-semibold">Account not found</div>
        <Link href="/accounts" className="text-sm text-blue-600 hover:text-blue-800">
          ← Back to accounts
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <Link href="/accounts" className="text-sm text-blue-600 hover:text-blue-800">
            ← All accounts
          </Link>
          <div className="mt-1 text-lg font-semibold">{account.name}</div>
          <div className="text-sm text-neutral-800">
            Current balance: <span className="font-medium">{formatMoney(account.current_balance, { currency: account.currency })}</span>
          </div>
        </div>
        <Link
          href={`/transactions/new?account=${accountId}`}
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
        <div className="grid gap-3 sm:grid-cols-2">
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
        {transactionsQuery.isLoading ? (
          <div className="text-sm text-neutral-800">Loading transactions…</div>
        ) : transactionsQuery.isError ? (
          <div className="text-sm text-red-700">Failed to load transactions.</div>
        ) : transactionsQuery.data.transactions.length === 0 ? (
          <div className="text-sm text-neutral-800">
            No transactions found for this account.
            {hasActiveFilters && " Try clearing filters."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-neutral-500">
                <tr>
                  <th className="py-2 pr-3">Date</th>
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Tag</th>
                  <th className="py-2 pr-3">Description</th>
                  <th className="py-2 pr-3 text-right">Amount</th>
                  <th className="py-2 pr-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {transactionsQuery.data.transactions.map((t) => (
                  <tr key={t.id} className="border-t border-neutral-200">
                    <td className="py-2 pr-3 text-neutral-900">
                      {t.transaction_date}
                      {t.updated_at && t.updated_at !== t.created_at && (
                        <span className="ml-2 text-xs text-neutral-500">(edited)</span>
                      )}
                    </td>
                    <td className="py-2 pr-3 text-neutral-900">
                      {t.transaction_type}
                      {t.related_account_name && (
                        <div className="text-xs text-neutral-500">
                          {t.transaction_type === "transfer" && parseFloat(t.amount) < 0 ? "to" : "from"} {t.related_account_name}
                        </div>
                      )}
                    </td>
                    <td className="py-2 pr-3 text-neutral-900">{t.tag}</td>
                    <td className="py-2 pr-3 text-neutral-900">{t.description ?? ""}</td>
                    <td className="py-2 pr-3 text-right font-medium text-neutral-900">
                      {formatMoney(t.amount, { currency: t.currency })}
                    </td>
                    <td className="py-2 pr-3">
                      {t.transaction_type !== "transfer" && (
                        <Link
                          href={`/transactions/${t.id}/edit`}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <div className="text-sm text-neutral-600">
        Showing {transactionsQuery.data?.transactions.length ?? 0} of {transactionsQuery.data?.total_count ?? 0} transactions
      </div>
    </div>
  );
}
