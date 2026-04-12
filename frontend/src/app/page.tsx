import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="container mx-auto flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <h1 className="text-4xl font-bold tracking-tight">Loyalty Platform</h1>
      <p className="text-muted-foreground">Multi-tenant loyalty cho SME</p>
      <div className="flex gap-4">
        <Link href="/login" className={buttonVariants()}>
          Đăng nhập
        </Link>
        <Link href="/register" className={buttonVariants({ variant: "outline" })}>
          Đăng ký
        </Link>
      </div>
    </main>
  );
}
