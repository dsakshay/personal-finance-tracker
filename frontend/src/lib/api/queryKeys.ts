export const queryKeys = {
  auth: {
    me: () => ["auth", "me"] as const,
  },
  accounts: {
    list: (params?: { currency?: string }) => ["accounts", "list", params ?? {}] as const,
  },
  transactions: {
    list: (params?: {
      account_id?: string;
      transaction_type?: string;
      tag?: string;
      limit?: number;
      offset?: number;
    }) => ["transactions", "list", params ?? {}] as const,
    detail: (id: string) => ["transactions", "detail", id] as const,
  },
  summary: {
    monthly: (params: { year: number; month: number; currency?: string }) =>
      ["summary", "monthly", params] as const,
  },
} as const;


