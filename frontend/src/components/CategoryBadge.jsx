const STYLES = {
  service: "bg-accent-soft text-accent-soft-text",
  faq: "bg-blue-50 text-blue-700",
  hours: "bg-violet-50 text-violet-700",
  location: "bg-orange-50 text-orange-700",
  policy: "bg-slate-100 text-slate-700",
  other: "bg-gray-100 text-gray-600",
};

const LABELS = {
  service: "Service",
  faq: "FAQ",
  hours: "Opening Hours",
  location: "Location",
  policy: "Policy",
  other: "Other",
};

export default function CategoryBadge({ category }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${STYLES[category] || STYLES.other}`}
    >
      {LABELS[category] || category}
    </span>
  );
}
