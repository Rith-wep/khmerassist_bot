import { BookOpen, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "../api/client";
import Button from "../components/Button";
import CategoryBadge from "../components/CategoryBadge";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { KnowledgeListSkeleton } from "../components/Skeleton";

const CATEGORIES = [
  { value: "service", label: "Service" },
  { value: "faq", label: "FAQ" },
  { value: "hours", label: "Opening Hours" },
  { value: "location", label: "Location" },
  { value: "policy", label: "Policy" },
  { value: "other", label: "Other" },
];

const EMPTY_FORM = {
  category: "service",
  title: "",
  content_en: "",
  content_km: "",
  price: "",
  sort_order: 0,
};

const fieldClass =
  "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-ink transition-colors duration-150 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";
const labelClass = "mb-1 block text-sm font-medium text-ink";

function ItemForm({ initial, onSubmit, onCancel, submitLabel }) {
  const [form, setForm] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await onSubmit({
        ...form,
        price: form.price || null,
        content_en: form.content_en || null,
        content_km: form.content_km || null,
        sort_order: Number(form.sort_order) || 0,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save. Please try again.");
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
    >
      {error && <p className="rounded-lg bg-error-soft px-3 py-2 text-sm text-error">{error}</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Category</label>
          <select
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
            className={fieldClass}
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelClass}>Price (optional)</label>
          <input
            type="text"
            value={form.price ?? ""}
            onChange={(e) => update("price", e.target.value)}
            placeholder="e.g. $15 or $20 - $40"
            className={fieldClass}
          />
        </div>
      </div>

      <div>
        <label className={labelClass}>Title</label>
        <input
          type="text"
          required
          value={form.title}
          onChange={(e) => update("title", e.target.value)}
          placeholder="e.g. Teeth cleaning"
          className={fieldClass}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>English content</label>
          <textarea
            rows={3}
            value={form.content_en ?? ""}
            onChange={(e) => update("content_en", e.target.value)}
            className={fieldClass}
          />
        </div>
        <div>
          <label className={labelClass}>Khmer content</label>
          <textarea
            rows={3}
            value={form.content_km ?? ""}
            onChange={(e) => update("content_km", e.target.value)}
            className={fieldClass}
          />
        </div>
      </div>

      <div className="flex items-center gap-2 pt-1">
        <Button type="submit" disabled={saving}>
          {saving ? "Saving..." : submitLabel}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

export default function KnowledgeEditor() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  async function loadItems() {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("/knowledge");
      setItems(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load knowledge items.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadItems();
  }, []);

  async function handleCreate(values) {
    await apiFetch("/knowledge", { method: "POST", body: values });
    setShowAddForm(false);
    await loadItems();
  }

  async function handleUpdate(id, values) {
    await apiFetch(`/knowledge/${id}`, { method: "PUT", body: values });
    setEditingId(null);
    await loadItems();
  }

  async function handleDelete(id) {
    if (!confirm("Delete this knowledge item?")) return;
    try {
      await apiFetch(`/knowledge/${id}`, { method: "DELETE" });
      await loadItems();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete item.");
    }
  }

  return (
    <div>
      <PageHeader
        title="Knowledge"
        description="What your assistant knows and answers customers with."
        action={
          !showAddForm && (
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="h-4 w-4" strokeWidth={2.5} />
              Add item
            </Button>
          )
        }
      />

      {error && (
        <p className="mb-4 rounded-lg bg-error-soft px-3 py-2 text-sm text-error">{error}</p>
      )}

      {showAddForm && (
        <div className="mb-6">
          <ItemForm
            initial={EMPTY_FORM}
            submitLabel="Add"
            onSubmit={handleCreate}
            onCancel={() => setShowAddForm(false)}
          />
        </div>
      )}

      {loading ? (
        <KnowledgeListSkeleton />
      ) : items.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No knowledge items yet"
          description="Add your services, hours, location, and FAQs so your assistant can answer customers accurately."
          action={
            !showAddForm && (
              <Button onClick={() => setShowAddForm(true)}>
                <Plus className="h-4 w-4" strokeWidth={2.5} />
                Add your first item
              </Button>
            )
          }
        />
      ) : (
        <div className="space-y-3">
          {items.map((item) =>
            editingId === item.id ? (
              <ItemForm
                key={item.id}
                initial={{
                  category: item.category,
                  title: item.title,
                  content_en: item.content_en || "",
                  content_km: item.content_km || "",
                  price: item.price || "",
                  sort_order: item.sort_order,
                }}
                submitLabel="Save"
                onSubmit={(values) => handleUpdate(item.id, values)}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div
                key={item.id}
                className="group rounded-xl border border-gray-200 bg-white p-4 transition-shadow duration-150 hover:shadow-md sm:p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <CategoryBadge category={item.category} />
                      {item.price && (
                        <span className="font-heading text-sm font-bold text-accent-dark">
                          {item.price}
                        </span>
                      )}
                    </div>
                    <h3 className="mt-2 truncate font-heading font-bold text-ink">{item.title}</h3>
                    {item.content_en && (
                      <p className="mt-1 text-sm text-ink-muted">{item.content_en}</p>
                    )}
                    {item.content_km && (
                      <p className="mt-1 text-sm text-ink-muted">{item.content_km}</p>
                    )}
                  </div>
                  <div className="flex shrink-0 gap-1 opacity-100 transition-opacity duration-150 sm:opacity-0 sm:group-hover:opacity-100">
                    <button
                      onClick={() => setEditingId(item.id)}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors duration-150 hover:bg-accent-soft hover:text-accent-dark"
                      aria-label="Edit"
                    >
                      <Pencil className="h-4 w-4" strokeWidth={2} />
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors duration-150 hover:bg-error-soft hover:text-error"
                      aria-label="Delete"
                    >
                      <Trash2 className="h-4 w-4" strokeWidth={2} />
                    </button>
                  </div>
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}
