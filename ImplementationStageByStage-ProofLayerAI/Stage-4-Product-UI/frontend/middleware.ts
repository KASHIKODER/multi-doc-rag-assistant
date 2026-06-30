import { NextResponse } from "next/server";
import { auth } from "./auth";

const protectedRoutes = [
  "/dashboard",
  "/documents",
  "/ask",
  "/history",
  "/settings",
  "/developer",
];

export default auth((request) => {
  const isLoggedIn = Boolean(request.auth);
  const pathname = request.nextUrl.pathname;

  const isProtectedRoute = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (!isLoggedIn && isProtectedRoute) {
    const loginUrl = new URL("/login", request.nextUrl.origin);
    loginUrl.searchParams.set("callbackUrl", pathname);

    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/documents/:path*",
    "/ask/:path*",
    "/history/:path*",
    "/settings/:path*",
    "/developer/:path*",
  ],
};