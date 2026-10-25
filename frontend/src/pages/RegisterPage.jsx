import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Mail, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import AuthLayout from "../components/auth/AuthLayout.jsx";
import FormField from "../components/auth/FormField.jsx";
import PasswordInput from "../components/auth/PasswordInput.jsx";
import SubmitButton from "../components/auth/SubmitButton.jsx";
import Alert from "../components/ui/Alert.jsx";
import Splash from "../components/ui/Splash.jsx";
import { PASSWORD_HINT, passwordStrength, validateRegister } from "../utils/validation.js";

const STRENGTH = [
  { label: "Too weak", bar: "bg-rose-500" },
  { label: "Weak", bar: "bg-rose-500" },
  { label: "Okay", bar: "bg-amber-400" },
  { label: "Good", bar: "bg-emerald-400" },
  { label: "Strong", bar: "bg-emerald-400" },
];

export default function RegisterPage() {
  const { status, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm_password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const timer = useRef(null);
  const submitting = useRef(false); // stops the 'already logged in' redirect while we show the success message

  useEffect(() => () => clearTimeout(timer.current), []);

  if (status === "loading") return <Splash />;
  if (status === "authenticated" && !success && !submitting.current) return <Navigate to="/chat" replace />;

  const set = (key) => (e) => {
    setForm((f) => ({ ...f, [key]: e.target.value }));
    if (errors[key]) setErrors((er) => ({ ...er, [key]: undefined }));
  };

  async function onSubmit(e) {
    e.preventDefault();
    if (loading || success) return;
    setFormError(null);
    const v = validateRegister(form);
    setErrors(v);
    if (Object.keys(v).length) return;
    setLoading(true);
    submitting.current = true;
    try {
      await register({ ...form, name: form.name.trim(), email: form.email.trim() });
      setSuccess(true); // the server signed us in; show feedback briefly, then open the app
      timer.current = setTimeout(() => navigate("/chat", { replace: true }), 1200);
    } catch (err) {
      submitting.current = false;
      setErrors(err.fieldErrors || {});
      setFormError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const strength = passwordStrength(form.password);

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Start your personalized fitness journey in seconds."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-emerald-300 hover:underline">Log in</Link></>}
    >
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        {success && <Alert type="success">Account created! Taking you to your coach...</Alert>}
        {formError && <Alert type="error">{formError}</Alert>}
        <FormField label="Full name" icon={User} autoComplete="name" placeholder="Ayesha Khan" value={form.name} onChange={set("name")} error={errors.name} maxLength={60} autoFocus />
        <FormField label="Email" icon={Mail} type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={set("email")} error={errors.email} />
        <div>
          <PasswordInput label="Password" autoComplete="new-password" placeholder="Create a password" value={form.password} onChange={set("password")} error={errors.password} hint={PASSWORD_HINT} maxLength={64} />
          {form.password && (
            <div className="mt-2 flex items-center gap-2" aria-live="polite">
              <div className="flex flex-1 gap-1">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className={`h-1.5 flex-1 rounded-full ${strength >= i ? STRENGTH[strength].bar : "bg-white/10"}`} />
                ))}
              </div>
              <span className="text-xs text-slate-400">{STRENGTH[strength].label}</span>
            </div>
          )}
        </div>
        <PasswordInput label="Confirm password" autoComplete="new-password" placeholder="Re-enter your password" value={form.confirm_password} onChange={set("confirm_password")} error={errors.confirm_password} maxLength={64} />
        <div className="pt-2">
          <SubmitButton loading={loading || success} loadingText={success ? "Redirecting..." : "Creating account..."}>Create account</SubmitButton>
        </div>
      </form>
    </AuthLayout>
  );
}
