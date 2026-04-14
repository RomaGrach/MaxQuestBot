import { buttonSecondaryClass, cx, panelClass, subtlePanelClass } from "./utils";

export function Button({ children, className, icon: Icon, ...props }) {
  return (
    <button className={cx(buttonSecondaryClass, className)} {...props}>
      {Icon ? <Icon className="h-4 w-4" /> : null}
      <span>{children}</span>
    </button>
  );
}

export function Field({ label, hint, children }) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-[color:var(--ink)]">{label}</span>
      {children}
      {hint ? <span className="text-xs text-[color:var(--muted)]">{hint}</span> : null}
    </label>
  );
}

export function StatusBadge({ value }) {
  const config = {
    draft: { label: "Черновик", className: "border-stone-300 bg-stone-100 text-stone-700" },
    published: { label: "Опубликован", className: "border-emerald-200 bg-emerald-50 text-emerald-800" },
    archived: { label: "Архив", className: "border-zinc-300 bg-zinc-100 text-zinc-700" },
    in_progress: { label: "В процессе", className: "border-amber-200 bg-amber-50 text-amber-800" },
    completed: { label: "Завершён", className: "border-emerald-200 bg-emerald-50 text-emerald-800" },
  }[value] || {
    label: value || "—",
    className: "border-stone-300 bg-stone-100 text-stone-700",
  };

  return (
    <span className={cx("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold", config.className)}>
      {config.label}
    </span>
  );
}

export function Notice({ notice, onClose }) {
  if (!notice) {
    return null;
  }

  const toneClass =
    notice.type === "error"
      ? "border-rose-200 bg-rose-50 text-rose-900"
      : notice.type === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-900"
        : "border-stone-200 bg-stone-50 text-stone-900";

  return (
    <div className={cx("flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm", toneClass)}>
      <div className="space-y-1">
        <p className="font-semibold">{notice.title}</p>
        <p>{notice.message}</p>
      </div>
      {onClose ? (
        <button className="text-xs font-semibold uppercase tracking-[0.08em]" onClick={onClose}>
          Закрыть
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className={cx(subtlePanelClass, "grid gap-3 p-5 text-sm text-[color:var(--muted)]")}>
      <div className="flex items-center gap-3 text-[color:var(--ink)]">
        <Icon className="h-5 w-5" />
        <p className="font-semibold">{title}</p>
      </div>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function SectionHeader({ title, description, actions }) {
  return (
    <div className="flex flex-col gap-3 border-b border-[color:var(--line)] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-[color:var(--ink)]">{title}</h2>
        {description ? <p className="text-sm text-[color:var(--muted)]">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function Surface({ children, className }) {
  return <div className={cx(panelClass, className)}>{children}</div>;
}
