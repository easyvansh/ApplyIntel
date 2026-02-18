"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import { format } from "date-fns";
import Papa from "papaparse";
import {
  Application,
  ApplicationCreate,
  Stats,
  Status,
  deleteApplication,
  fetchApplications,
  fetchStats,
  restoreApplication,
  updateApplicationStatus,
  createApplication,
} from "../lib/api";

ChartJS.register(ArcElement, Tooltip, Legend);

const STATUS_OPTIONS: Status[] = [
  "saved",
  "applied",
  "interview",
  "offer",
  "rejected",
];

const DEFAULT_FORM = {
  company: "",
  role: "",
  location: "",
  url: "",
  status: "applied" as Status,
  date_applied: format(new Date(), "yyyy-MM-dd"),
  next_action_date: "",
  notes: "",
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  try {
    return format(new Date(value), "MMM dd, yyyy");
  } catch {
    return value;
  }
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    total: 0,
    counts: {},
    response_rate: 0,
    due_today: 0,
    saved_jobs: 0,
    interviews: 0,
  });
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<Status | "">("");
  const [hasLinkFilter, setHasLinkFilter] = useState<"" | "yes" | "no">("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [modalId, setModalId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ id: number } | null>(null);
  const undoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pageSize = 10;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const chartData = useMemo(() => {
    const counts = stats.counts || {};
    const labels = STATUS_OPTIONS;
    return {
      labels,
      datasets: [
        {
          data: labels.map((label) => counts[label] || 0),
          backgroundColor: [
            "rgba(108, 184, 255, 0.7)",
            "rgba(61, 213, 167, 0.7)",
            "rgba(242, 184, 75, 0.7)",
            "rgba(192, 132, 252, 0.7)",
            "rgba(255, 107, 107, 0.7)",
          ],
          borderColor: "rgba(255, 255, 255, 0.08)",
          borderWidth: 1,
        },
      ],
    };
  }, [stats]);

  const chartOptions: ChartOptions<"pie"> = {
    plugins: {
      legend: {
        labels: {
          color: "#a7b1c3",
        },
      },
    },
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        q: query.trim() || undefined,
        status: statusFilter || undefined,
        has_link:
          hasLinkFilter === "yes"
            ? true
            : hasLinkFilter === "no"
              ? false
              : undefined,
        sort_order: sortOrder,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      };
      const [statsData, list] = await Promise.all([
        fetchStats(),
        fetchApplications(params),
      ]);
      setStats(statsData);
      setApplications(list.items);
      setTotal(list.total);
    } catch (err) {
      setError("Unable to load applications. Check the API server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [query, statusFilter, hasLinkFilter, sortOrder, page]);

  const handleStatusUpdate = async (id: number, status: Status) => {
    await updateApplicationStatus(id, status);
    await loadData();
  };

  const handleDelete = async () => {
    if (modalId === null) return;
    await deleteApplication(modalId);
    setToast({ id: modalId });
    setModalId(null);
    if (undoTimer.current) {
      clearTimeout(undoTimer.current);
    }
    undoTimer.current = setTimeout(() => {
      setToast(null);
    }, 5000);
    await loadData();
  };

  const handleUndo = async () => {
    if (!toast) return;
    await restoreApplication(toast.id);
    setToast(null);
    if (undoTimer.current) {
      clearTimeout(undoTimer.current);
    }
    await loadData();
  };

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    const payload: ApplicationCreate = {
      company: form.company.trim(),
      role: form.role.trim(),
      location: form.location.trim() || null,
      url: form.url.trim() || null,
      status: form.status,
      date_applied: form.date_applied,
      next_action_date: form.next_action_date || null,
      notes: form.notes.trim() || null,
    };
    await createApplication(payload);
    setForm({ ...DEFAULT_FORM, date_applied: form.date_applied });
    setPage(1);
    await loadData();
  };

  const handleExport = () => {
    const rows = applications.map((app) => ({
      company: app.company,
      role: app.role,
      status: app.status,
      date_applied: app.date_applied,
      next_action_date: app.next_action_date || "",
      location: app.location || "",
      url: app.url || "",
      notes: app.notes || "",
    }));
    const csv = Papa.unparse(rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "jobtrackr_export.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <div className="container">
      <motion.div
        className="header"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div>
          <div className="badge">ApplyIntel</div>
          <h1 className="title">ApplyIntel Command Center</h1>
          <p className="subtitle">
            Track every application, track follow-ups, and keep the pipeline
            moving without spreadsheet chaos.
          </p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={handleExport}>
            Export CSV
          </button>
          <button
            className="btn btn-muted"
            onClick={() => {
              setPage(1);
              loadData();
            }}
          >
            Refresh
          </button>
        </div>
      </motion.div>

      <div className="grid">
        <div className="card">
          <h3>Total Applications</h3>
          <div className="value">{stats.total}</div>
        </div>
        <div className="card">
          <h3>Interviews</h3>
          <div className="value">{stats.interviews}</div>
        </div>
        <div className="card">
          <h3>Offers</h3>
          <div className="value">{stats.counts?.offer || 0}</div>
        </div>
        <div className="card">
          <h3>Response Rate</h3>
          <div className="value">{Math.round(stats.response_rate * 100)}%</div>
        </div>
      </div>

      <div className="panel">
        <div className="grid" style={{ marginBottom: 0 }}>
          <div>
            <h3 style={{ margin: 0 }}>Status Mix</h3>
            <Pie data={chartData} options={chartOptions} />
          </div>
          <div>
            <h3 style={{ margin: 0 }}>Follow-up Queue</h3>
            <div className="grid" style={{ marginTop: 12 }}>
              <div className="card">
                <h3>Due Today</h3>
                <div className="value">{stats.due_today}</div>
              </div>
              <div className="card">
                <h3>Saved Jobs</h3>
                <div className="value">{stats.saved_jobs}</div>
              </div>
              <div className="card">
                <h3>Interviews</h3>
                <div className="value">{stats.interviews}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Add Application</h3>
        <form className="controls" onSubmit={handleCreate}>
          <input
            className="input"
            placeholder="Company"
            value={form.company}
            onChange={(event) => setForm({ ...form, company: event.target.value })}
            required
          />
          <input
            className="input"
            placeholder="Role"
            value={form.role}
            onChange={(event) => setForm({ ...form, role: event.target.value })}
            required
          />
          <input
            className="input"
            placeholder="Location"
            value={form.location}
            onChange={(event) => setForm({ ...form, location: event.target.value })}
          />
          <input
            className="input"
            placeholder="Link"
            value={form.url}
            onChange={(event) => setForm({ ...form, url: event.target.value })}
          />
          <select
            className="select"
            value={form.status}
            onChange={(event) =>
              setForm({ ...form, status: event.target.value as Status })
            }
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <input
            className="input"
            type="date"
            value={form.date_applied}
            onChange={(event) =>
              setForm({ ...form, date_applied: event.target.value })
            }
            required
          />
          <input
            className="input"
            type="date"
            value={form.next_action_date}
            onChange={(event) =>
              setForm({ ...form, next_action_date: event.target.value })
            }
          />
          <input
            className="input"
            placeholder="Notes"
            value={form.notes}
            onChange={(event) => setForm({ ...form, notes: event.target.value })}
          />
          <button className="btn btn-primary" type="submit">
            Add Application
          </button>
        </form>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Pipeline</h3>
        <div className="controls">
          <input
            className="input"
            placeholder="Search company or role"
            value={query}
            onChange={(event) => {
              setPage(1);
              setQuery(event.target.value);
            }}
          />
          <select
            className="select"
            value={statusFilter}
            onChange={(event) => {
              setPage(1);
              setStatusFilter(event.target.value as Status | "");
            }}
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <select
            className="select"
            value={hasLinkFilter}
            onChange={(event) => {
              setPage(1);
              setHasLinkFilter(event.target.value as "" | "yes" | "no");
            }}
          >
            <option value="">All links</option>
            <option value="yes">Has link</option>
            <option value="no">Missing link</option>
          </select>
          <select
            className="select"
            value={sortOrder}
            onChange={(event) => {
              setPage(1);
              setSortOrder(event.target.value as "asc" | "desc");
            }}
          >
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </div>

        {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Applied</th>
                <th>Next Action</th>
                <th>Location</th>
                <th>Link</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={9}>No applications found.</td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id}>
                    <td>{app.company}</td>
                    <td>{app.role}</td>
                    <td>
                      <select
                        className="select"
                        value={app.status}
                        onChange={(event) =>
                          handleStatusUpdate(
                            app.id,
                            event.target.value as Status
                          )
                        }
                      >
                        {STATUS_OPTIONS.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>{formatDate(app.date_applied)}</td>
                    <td>{formatDate(app.next_action_date)}</td>
                    <td>{app.location || "—"}</td>
                    <td>
                      {app.url ? (
                        <a className="link" href={app.url} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{app.notes || "—"}</td>
                    <td>
                      <button
                        className="btn btn-muted"
                        onClick={() => setModalId(app.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        <div className="pagination">
          <span>
            Page {page} of {totalPages} · {total} records
          </span>
          <div className="actions">
            <button
              className="btn btn-muted"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Prev
            </button>
            <button
              className="btn btn-muted"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {modalId !== null && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>Delete application?</h3>
            <p>This will move the record to deleted. You can undo for 5 seconds.</p>
            <div className="actions">
              <button className="btn btn-primary" onClick={handleDelete}>
                Confirm Delete
              </button>
              <button className="btn btn-muted" onClick={() => setModalId(null)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="toast">
          <span>Application deleted.</span>
          <button className="btn btn-primary" onClick={handleUndo}>
            Undo
          </button>
        </div>
      )}
    </div>
  );
}
