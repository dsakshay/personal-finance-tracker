"use client";

import * as React from "react";

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={[
        "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900",
        "placeholder:text-neutral-400",
        "focus:outline-none focus:ring-2 focus:ring-neutral-900/20 focus:border-neutral-400",
        "disabled:cursor-not-allowed disabled:opacity-60",
        props.className ?? "",
      ].join(" ")}
    />
  );
}


