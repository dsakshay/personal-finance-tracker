"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { formatMoney } from "@/lib/money/money";

export default function AccountsPage() {
  const q = useQuery({
    queryKey: queryKeys.accounts.list({}),
    queryFn: () => api.accounts.list(),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-lg font-semibold">Accounts</div>
          <div className="text-sm text-neutral-800">Current balances are derived from transactions.</div>
        </div>
        <Link
          href="/accounts/new"
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800"
        >
          New account
        </Link>
      </div>

      <Card>
        {q.isLoading ? (
          <div className="text-sm text-neutral-800">Loading accounts…</div>
        ) : q.isError ? (
          <div className="text-sm text-red-700">Failed to load accounts.</div>
        ) : !q.data ? (
          <div className="text-sm text-neutral-800">No data.</div>
        ) : q.data.accounts.length === 0 ? (
          <div className="text-sm text-neutral-800">
            No accounts yet. Create your first one.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-neutral-500">
                <tr>
                  <th className="py-2 pr-3">Name</th>
                  <th className="py-2 pr-3">Currency</th>
                  <th className="py-2 pr-3">Opening</th>
                  <th className="py-2 pr-3">Current</th>
                  <th className="py-2 pr-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {q.data.accounts.map((a) => (
                  <tr key={a.id} className="border-t border-neutral-200">
                    <td className="py-2 pr-3 font-medium text-neutral-900">{a.name}</td>
                    <td className="py-2 pr-3 text-neutral-900">{a.currency}</td>
                    <td className="py-2 pr-3 text-neutral-900">
                      {formatMoney(a.opening_balance, { currency: a.currency })}
                    </td>
                    <td className="py-2 pr-3 text-neutral-900">
                      {formatMoney(a.current_balance, { currency: a.currency })}
                    </td>
                    <td className="py-2 pr-3">
                      <Link
                        href={`/accounts/${a.id}/transactions`}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        View transactions
                      </Link>
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


