import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch, ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import Button from "../components/Button";

const BUSINESS_TYPES = [
  { value: "clinic", label: "Clinic" },
  { value: "shop", label: "Shop" },
  { value: "real_estate", label: "Real Estate" },
  { value: "other", label: "Other" },
];

const inputClass =
  "w-full rounded-lg border border-shell-border bg-base px-3 py-2.5 text-sm text-shell-text placeholder-shell-text-muted/60 transition-colors duration-150 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";
const labelClass = "mb-1.5 block text-sm font-medium text-shell-text-muted";

export default function SignUp() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [businessType, setBusinessType] = useState("clinic");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiFetch("/auth/signup", {
        method: "POST",
        auth: false,
        body: {
          email,
          password,
          business_name: businessName,
          business_type: businessType,
        },
      });
      login(data.access_token, data.business_name);
      navigate("/knowledge");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-accent font-heading text-lg font-extrabold text-white">
            K
          </div>
          <h1 className="font-heading text-2xl font-bold text-shell-text">Create your account</h1>
          <p className="mt-1 text-sm text-shell-text-muted">
            Set up your business's AI assistant
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-shell-border bg-surface p-6 shadow-xl"
        >
          {error && (
            <p className="rounded-lg bg-error-soft px-3 py-2 text-sm text-error">{error}</p>
          )}

          <div>
            <label className={labelClass}>Business name</label>
            <input
              type="text"
              required
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              className={inputClass}
              placeholder="Sok Dara Dental Clinic"
            />
          </div>

          <div>
            <label className={labelClass}>Business type</label>
            <select
              value={businessType}
              onChange={(e) => setBusinessType(e.target.value)}
              className={inputClass}
            >
              {BUSINESS_TYPES.map((t) => (
                <option key={t.value} value={t.value} className="bg-base">
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelClass}>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="you@business.com"
            />
          </div>

          <div>
            <label className={labelClass}>Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              placeholder="At least 8 characters"
            />
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-shell-text-muted">
          Already have an account?{" "}
          <Link to="/signin" className="font-semibold text-accent hover:text-accent-dark">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
