export type UUID = string;
export type ISO8601Date = string; // YYYY-MM-DD
export type ISO8601Timestamp = string; // ISO 8601, typically with timezone
export type CurrencyCode = string; // ISO 4217 (e.g., "INR")
export type DecimalString = string; // e.g., "100.50" or "-500.00"

export type TransactionType = "income" | "expense" | "transfer";

// ---- Auth ----
export interface SignupRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer" | string;
}

export interface UserRead {
  id: UUID;
  email: string;
  created_at: ISO8601Timestamp;
}

// ---- Accounts ----
export interface CreateAccountRequest {
  name: string;
  currency: CurrencyCode;
  opening_balance?: DecimalString; // defaults to "0.00"
}

export interface Account {
  id: UUID;
  name: string;
  currency: CurrencyCode;
  opening_balance: DecimalString;
  current_balance: DecimalString;
  created_at: ISO8601Timestamp;
}

export interface AccountListResponse {
  accounts: Account[];
  total_count: number;
}

// ---- Transactions ----
export interface CreateTransactionRequest {
  account_id: UUID;
  amount: DecimalString; // positive, backend applies sign by type
  currency: CurrencyCode;
  transaction_type: Exclude<TransactionType, "transfer">; // /transactions rejects transfer
  tag: string;
  payment_method?: string;
  description?: string;
  transaction_date: ISO8601Date;
}

export interface CreateTransferRequest {
  account_id: UUID; // source
  related_account_id: UUID; // destination
  amount: DecimalString; // positive
  currency: CurrencyCode;
  transaction_type?: "transfer";
  tag?: string; // default "transfer"
  payment_method?: string;
  description?: string;
  transaction_date: ISO8601Date;
}

export interface UpdateTransactionRequest {
  account_id?: UUID;
  amount?: DecimalString; // positive, backend applies sign
  tag?: string;
  payment_method?: string;
  description?: string;
  transaction_date?: ISO8601Date;
}

export interface Transaction {
  id: UUID;
  account_id: UUID;
  account_name: string;
  amount: DecimalString; // signed
  currency: CurrencyCode;
  transaction_type: TransactionType;
  tag: string;
  payment_method: string | null;
  related_account_id: UUID | null;
  related_account_name: string | null;
  description: string | null;
  transaction_date: ISO8601Date;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp | null;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface TransferResponse {
  transfer_id: UUID;
  transactions: Transaction[];
}

// ---- Summary ----
export interface MonthlySummary {
  period: {
    year: number;
    month: number;
    month_name: string;
    start_date: ISO8601Date;
    end_date: ISO8601Date;
  };
  summary: {
    total_income: DecimalString;
    total_expenses: DecimalString;
    net_savings: DecimalString;
    currency: CurrencyCode | "MIXED";
  };
  by_tag: Array<{
    tag: string;
    total: DecimalString;
    count: number;
    currency: CurrencyCode | "MIXED";
  }>;
  by_account: Array<{
    account_id: UUID;
    account_name: string;
    opening_balance: DecimalString;
    closing_balance: DecimalString;
    net_change: DecimalString;
    currency: CurrencyCode;
    transaction_count: number;
  }>;
  top_expenses: Array<{
    id: UUID;
    account_name: string;
    amount: DecimalString; // negative
    currency: CurrencyCode;
    tag: string;
    description: string | null;
    transaction_date: ISO8601Date;
  }>;
}


