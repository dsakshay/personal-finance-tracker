"use client";

import * as React from "react";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={[
        "rounded-lg border border-neutral-200 bg-white p-4 shadow-sm",
        className ?? "",
      ].join(" ")}
    />
  );
}


