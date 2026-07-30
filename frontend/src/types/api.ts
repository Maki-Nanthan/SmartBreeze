export interface ClassroomStatusResponse {
  student_count: number;
  occupancy_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  ac_status: boolean;
  temperature: number | null;
  control_mode: 'EDGE_AI' | 'MANUAL' | 'AI_SIMULATION' | string;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
}

export interface ApiConnectionStatus {
  health: boolean;
  status: boolean;
  message: string;
}
