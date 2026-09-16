import axios from "axios";

export type Status = "saved" | "applied" | "interview" | "rejected" | "offer";
export type SortOrder = "asc" | "desc";

export interface Application {
  id: number;
  company: string;
  role: string;
  location: string | null;
  url: string | null;
  status: Status;
  date_applied: string;
  next_action_date: string | null;
  notes: string | null;
  created_at: string;
}

export interface ApplicationCreate {
  company: string;
  role: string;
  location: string | null;
  url: string | null;
  status: Status;
  date_applied: string;
  next_action_date: string | null;
  notes: string | null;
}

export interface Stats {
  total: number;
  counts: Record<string, number>;
  response_rate: number;
  due_today: number;
  saved_jobs: number;
  interviews: number;
}

export interface ApplicationListResponse {
  items: Application[];
  total: number;
}

export interface Readiness {
  status: "ready";
  database: "connected";
  requestId: string | null;
}

interface APIErrorResponse {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
  };
  detail?: string;
}

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
});

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError<APIErrorResponse>(error)) {
    return fallback;
  }

  return error.response?.data?.error?.message || error.response?.data?.detail || fallback;
}

export async function fetchApplications(params: {
  q?: string;
  status?: Status | "";
  has_link?: boolean | "";
  sort_order?: SortOrder;
  limit?: number;
  offset?: number;
}) {
  const response = await api.get<ApplicationListResponse>("/applications", {
    params,
  });
  return response.data;
}

export async function createApplication(payload: ApplicationCreate) {
  const response = await api.post<Application>("/applications", payload);
  return response.data;
}

export async function updateApplicationStatus(id: number, status: Status) {
  const response = await api.patch<Application>(`/applications/${id}`, { status });
  return response.data;
}

export async function deleteApplication(id: number) {
  const response = await api.delete<Application>(`/applications/${id}`);
  return response.data;
}

export async function restoreApplication(id: number) {
  const response = await api.post<Application>(`/applications/${id}/restore`);
  return response.data;
}

export async function fetchStats() {
  const response = await api.get<Stats>("/stats");
  return response.data;
}

export async function fetchReadiness(): Promise<Readiness> {
  const response = await api.get<Omit<Readiness, "requestId">>("/health/ready");
  return {
    ...response.data,
    requestId: response.headers["x-request-id"] || null,
  };
}
