import Decimal from "decimal.js";
import type { DecimalString } from "../api/types";

export function money(value: DecimalString): Decimal {
  return new Decimal(value);
}

export function formatMoney(value: DecimalString, opts?: { currency?: string }): string {
  const d = money(value);
  const sign = d.isNeg() ? "-" : "";
  const abs = d.abs().toFixed(2);
  const prefix = opts?.currency ? `${opts.currency} ` : "";
  return `${sign}${prefix}${abs}`;
}


