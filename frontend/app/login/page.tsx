import { AuthForm } from "@/components/auth-form";

export const metadata = { title: "Log in — FinTrack" };

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
