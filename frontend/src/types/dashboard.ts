export interface OccupancyHistoryEntry {
  id: number;
  student_count: number;
  occupancy_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  control_mode: string;
  timestamp: string;
}

export interface ACEventEntry {
  id: number;
  ac_status: boolean;
  temperature: number | null;
  reason: string | null;
  timestamp: string;
}

export interface RunningTimeResponse {
  total_minutes: number;
}
