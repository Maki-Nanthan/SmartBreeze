import { ClassroomStatusResponse, HealthResponse } from '../types/api';
import { ACEventEntry, OccupancyHistoryEntry, RunningTimeResponse } from '../types/dashboard';

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function withApiPrefix(path: string): string {
  return path.startsWith('/api') ? path : `/api${path.startsWith('/') ? path : `/${path}`}`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${withApiPrefix(path)}`, options);
  } catch (err) {
    throw new Error('Connection refused: Backend server is unreachable. Make sure the FastAPI backend is running on port 8000.');
  }

  const contentType = response.headers.get('content-type') || '';

  if (!response.ok) {
    let message = 'Request failed';
    try {
      if (contentType.includes('application/json')) {
        const json = await response.json();
        message = json.detail || json.message || 'Request failed';
      } else {
        message = await response.text();
      }
    } catch (parseErr) {
      message = `HTTP Error ${response.status}: Unable to parse error details`;
    }
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (!contentType.includes('application/json')) {
    let body = '';
    try {
      body = await response.text();
    } catch {
      body = '[Unreadable response body]';
    }
    throw new Error(`Expected JSON response from the API, but received non-JSON content. Details: ${body.slice(0, 140)}`);
  }

  try {
    return await response.json() as T;
  } catch (err) {
    throw new Error('Invalid JSON format: Received malformed response from the backend');
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function fetchStatus(): Promise<ClassroomStatusResponse> {
  return request<ClassroomStatusResponse>('/classroom/state');
}

export async function fetchOccupancyHistory(): Promise<OccupancyHistoryEntry[]> {
  return request<OccupancyHistoryEntry[]>('/occupancy-history');
}

export async function fetchAcEvents(): Promise<ACEventEntry[]> {
  return request<ACEventEntry[]>('/ac-events');
}

export async function fetchRunningTime(): Promise<RunningTimeResponse> {
  return request<RunningTimeResponse>('/ac-running-time');
}

export async function postManualControl(payload: Record<string, unknown>): Promise<ClassroomStatusResponse> {
  return request<ClassroomStatusResponse>('/manual-control', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function postOccupancy(payload: Record<string, unknown>): Promise<ClassroomStatusResponse> {
  return request<ClassroomStatusResponse>('/occupancy', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}
