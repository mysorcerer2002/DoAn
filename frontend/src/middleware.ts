import { NextResponse, type NextRequest } from "next/server";

const HOST_TO_PATH: Record<string, string> = {
  "member.ecom-bill.com": "/member",
  "admin.ecom-bill.com": "/admin",
  "pos.ecom-bill.com": "/merchant/pos/transactions/new",
  "merchant.ecom-bill.com": "/merchant",
};

export function middleware(req: NextRequest) {
  const host = (req.headers.get("host") ?? "").split(":")[0].toLowerCase();
  const target = HOST_TO_PATH[host];
  if (!target) return NextResponse.next();

  const { pathname } = req.nextUrl;
  if (pathname === "/" || pathname === "") {
    const url = req.nextUrl.clone();
    url.pathname = target;
    return NextResponse.rewrite(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|sw.js|favicon.ico).*)"],
};
