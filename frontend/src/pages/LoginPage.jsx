import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Mail } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import AuthLayout from "../components/auth/AuthLayout.jsx";
import FormField from "../components/auth/FormField.jsx";
import PasswordInput from "../components/auth/PasswordInput.jsx";
import SubmitButton from "../components/auth/SubmitButton.jsx";
import Alert from "../components/ui/Alert.jsx";
import Splash from "../components/ui/Splash.jsx";
import { validateLogin } from "../utils/validation.js";

export default function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [loading, setLoading] = useState(false);

  if (status === "loading") return <Splash />;
  if (status === "authenticated") return <Navigate to="/chat" replace />;

  const set = (key) => (e) => {
    setForm((f) => ({ ...f, [key]: e.target.value }));
    if (errors[key]) setErrors((er) => ({ ...er, [key]: undefined }));
  };

  async function onSubmit(e) {
    e.preventDefault();
    if (loading) return;
    setFormError(null);
    const v = validateLogin(form);
    setErrors(v);
    if (Object.keys(v).length) return;
    setLoading(true);
    try {
      await login(form.email.trim(), form.password);
      navigate(location.state?.from || "/chat", { replace: true });
    } catch (err) {
      setErrors(err.fieldErrors || {});
      setFormError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue your health journey."
      footer={<>New here? <Link to="/register" className="font-semibold text-emerald-300 hover:underline">Create an account</Link></>}
    >
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        {formError && <Alert type="error">{formError}</Alert>}
        <FormField label="Email" icon={Mail} type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={set("email")} error={errors.email} autoFocus />
        <PasswordInput label="Password" autoComplete="current-password" placeholder="Your password" value={form.password} onChange={set("password")} error={errors.password} />
        <div className="pt-2">
          <SubmitButton loading={loading} loadingText="Logging in...">Log in</SubmitButton>
        </div>
      </form>
    </AuthLayout>
  );
}
