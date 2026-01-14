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

      <Card>
        {q.isLoading ? (
          <div className="text-sm text-neutral-800">Loading summary…</div>
        ) : q.isError ? (
          <div className="text-sm text-red-700">Failed to load summary.</div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <div className="text-xs text-neutral-500">Total income</div>
              <div className="text-lg font-semibold">
                {formatMoney(q.data.summary.total_income, { currency: q.data.summary.currency })}
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-500">Total expenses</div>
              <div className="text-lg font-semibold">
                {formatMoney(q.data.summary.total_expenses, { currency: q.data.summary.currency })}
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-500">Net savings</div>
              <div className="text-lg font-semibold">
                {formatMoney(q.data.summary.net_savings, { currency: q.data.summary.currency })}
              </div>
            </div>
          </div>
        )}
      </Card>

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


