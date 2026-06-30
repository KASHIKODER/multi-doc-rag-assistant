"use client";

import Image from "next/image";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { APP_ROUTES } from "@/lib/constants";
import { Button } from "@/components/ui/Button";

function getInitials(name?: string | null, email?: string | null) {
  const source = name || email || "User";

  return source
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-xs font-semibold text-slate-500">
        ...
      </div>
    );
  }

  if (!session?.user) {
    return (
      <Link
        href={APP_ROUTES.login}
        className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-[#0F172A] transition hover:border-[#2563EB]"
      >
        Sign in
      </Link>
    );
  }

  const user = session.user;
  const initials = getInitials(user.name, user.email);

  return (
    <div className="flex items-center gap-3">
      <div className="hidden text-right md:block">
        <p className="text-sm font-semibold text-[#0F172A]">
          {user.name ?? "GitHub User"}
        </p>

        {user.email ? (
          <p className="mt-0.5 text-xs text-slate-500">{user.email}</p>
        ) : null}
      </div>

      {user.image ? (
        <Image
          src={user.image}
          alt={user.name ?? "User avatar"}
          width={40}
          height={40}
          className="h-10 w-10 rounded-full border border-slate-200 object-cover"
        />
      ) : (
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-sm font-semibold text-[#0F172A]">
          {initials}
        </div>
      )}

      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => signOut({ callbackUrl: "/login" })}
      >
        Logout
      </Button>
    </div>
  );
}