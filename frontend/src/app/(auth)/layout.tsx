export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-neutral-50">
      <div className="mx-auto flex min-h-dvh w-full max-w-md items-center px-4">
        <div className="w-full">{children}</div>
      </div>
    </div>
  );
}


