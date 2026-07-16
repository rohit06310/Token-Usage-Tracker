import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function HomePage() {
  const sessionCookie = (await cookies()).get("ai_session");
  if (sessionCookie?.value) {
    redirect("/dashboard");
  } else {
    redirect("/login");
  }
}
