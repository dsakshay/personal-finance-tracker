"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { formatMoney } from "@/lib/money/money";

function nowYearMonth(): { year: number; month: number } {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1 };
}

export default function DashboardPage() {
  const ym = useMemo(() => nowYearMonth(), []);
  const [year, setYear] = useState(ym.year);
  const [month, setMonth] = useState(ym.month);

  const q = useQuery({
    queryKey: queryKeys.summary.monthly({ year, month }),
    queryFn: () => api.summary.monthly({ year, month }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-lg font-semibold">Dashboard</div>
          <div className="text-sm text-neutral-800">Monthly summary</div>
        </div>
        <div className="flex items-center gap-2">
          <input
            className="w-24 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
            type="number"
            min={2000}
            max={3000}
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          />
          <select
            className="w-28 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>
                {String(m).padStart(2, "0")}
              </option>
            ))}
          </select>
          <Button
            variant="secondary"
            onClick={() => {
              const { year: y, month: m } = nowYearMonth();
              setYear(y);
              setMonth(m);
            }}
          >
            Today
          </Button>
        </div>
      </div>

      {/* Total Balance - Center Display */}
      {q.isLoading ? (
        <Card>
          <div className="text-sm text-neutral-800">Loading summary…</div>
        </Card>
      ) : q.isError ? (
        <Card>
          <div className="text-sm text-red-700">Failed to load summary.</div>
        </Card>
      ) : (
        <>
          <Card>
            <div className="text-center">
              <div className="text-sm text-neutral-600 mb-2">Total Balance (Current Month End)</div>
              <div className="text-4xl font-bold text-neutral-900">
                {q.data && formatMoney(
                  q.data.by_account.reduce((sum, acc) => sum + parseFloat(acc.closing_balance), 0).toFixed(2),
                  { currency: q.data.summary.currency }
                )}
              </div>
            </div>
          </Card>

          {/* Overall Summary */}
          <Card>
            <div className="mb-3 text-sm font-semibold">Monthly Overview</div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <div className="text-xs text-neutral-600">Total income</div>
                <div className="text-lg font-semibold text-green-600">
                  {formatMoney(q.data.summary.total_income, { currency: q.data.summary.currency })}
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-600">Total expenses</div>
                <div className="text-lg font-semibold text-red-600">
                  {formatMoney(q.data.summary.total_expenses, { currency: q.data.summary.currency })}
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-600">Net savings</div>
                <div className="text-lg font-semibold text-blue-600">
                  {formatMoney(q.data.summary.net_savings, { currency: q.data.summary.currency })}
                </div>
              </div>
            </div>
          </Card>

          {/* Per Account Breakdown */}
          {q.data.by_account.length > 0 && (
            <Card>
              <div className="mb-3 text-sm font-semibold">By Account</div>
              <div className="space-y-4">
                {q.data.by_account.map((acc) => (
                  <div key={acc.account_id} className="border-b border-neutral-200 pb-3 last:border-0">
                    <div className="mb-2 font-medium text-neutral-900">{acc.account_name}</div>
                    <div className="grid gap-3 sm:grid-cols-4 text-sm">
                      <div>
                        <div className="text-xs text-neutral-600">Opening</div>
                        <div className="font-medium">{formatMoney(acc.opening_balance, { currency: acc.currency })}</div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-600">Current</div>
                        <div className="font-medium">{formatMoney(acc.closing_balance, { currency: acc.currency })}</div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-600">Net Change</div>
                        <div className={`font-medium ${parseFloat(acc.net_change) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatMoney(acc.net_change, { currency: acc.currency })}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-600">Transactions</div>
                        <div className="font-medium">{acc.transaction_count}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {q.data ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <div className="mb-3 text-sm font-semibold">Top tags</div>
            {q.data.by_tag.length === 0 ? (
              <div className="text-sm text-neutral-800">No tagged activity this month.</div>
            ) : (
              <div className="space-y-2">
                {q.data.by_tag.slice(0, 6).map((t) => (
                  <div key={t.tag} className="flex items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{t.tag}</div>
                      <div className="text-xs text-neutral-500">{t.count} txns</div>
                    </div>
                    <div className="font-medium">
                      {formatMoney(t.total, { currency: t.currency })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <div className="mb-3 text-sm font-semibold">Top expenses</div>
            {q.data.top_expenses.length === 0 ? (
              <div className="text-sm text-neutral-800">No expenses this month.</div>
            ) : (
              <div className="space-y-2">
                {q.data.top_expenses.map((e) => (
                  <div key={e.id} className="flex items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <div className="truncate font-medium">{e.tag}</div>
                      <div className="text-xs text-neutral-500">
                        {e.account_name} • {e.transaction_date}
                      </div>
                    </div>
                    <div className="font-medium">{formatMoney(e.amount, { currency: e.currency })}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      ) : null}
    </div>
  );
}


