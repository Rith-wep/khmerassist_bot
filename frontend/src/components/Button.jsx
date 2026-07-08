const VARIANTS = {
  primary:
    "bg-accent text-white hover:bg-accent-dark focus-visible:ring-accent shadow-sm",
  secondary:
    "border border-gray-300 bg-white text-ink hover:bg-gray-50 focus-visible:ring-accent",
  destructive:
    "border border-error/30 text-error hover:bg-error-soft focus-visible:ring-error",
  ghost: "text-ink-muted hover:bg-gray-100 focus-visible:ring-accent",
};

export default function Button({
  variant = "primary",
  className = "",
  disabled,
  children,
  ...props
}) {
  return (
    <button
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
