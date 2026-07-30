import { useEffect, useMemo, useState } from 'react';
import { DashboardMetricCard } from '../components/DashboardMetricCard';
import { DashboardSection } from '../components/DashboardSection';
import { fetchHealth, fetchStatus, postOccupancy } from '../services/dashboardApi';
import { ClassroomStatusResponse, HealthResponse } from '../types/api';

export function SimulatorPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<ClassroomStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [autoSimulation, setAutoSimulation] = useState(false);

  const loadData = async () => {
    try {
      const [nextHealth, nextStatus] = await Promise.all([fetchHealth(), fetchStatus()]);
      setHealth(nextHealth);
      setStatus(nextStatus);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load simulator state');
    }
  };

  useEffect(() => {
    void loadData();
    const interval = window.setInterval(() => {
      void loadData();
    }, 5000);

    return () => {
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!autoSimulation) return;
    const interval = window.setInterval(async () => {
      if (!status) return;
      const currentCount = status.student_count ?? 0;
      const nextCount = currentCount >= 10 ? 0 : currentCount + 3;
      try {
        const nextStatus = await postOccupancy({ student_count: nextCount });
        setStatus(nextStatus);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Auto simulation update failed');
      }
    }, 3000);

    return () => {
      window.clearInterval(interval);
    };
  }, [autoSimulation, status]);

  const updateOccupancyLevel = async (nextCount: number) => {
    if (!status) return;
    setBusy(true);
    try {
      const nextStatus = await postOccupancy({ student_count: nextCount });
      setStatus(nextStatus);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update occupancy');
    } finally {
      setBusy(false);
    }
  };

  const handleAddStudent = async () => {
    const currentCount = status?.student_count ?? 0;
    await updateOccupancyLevel(currentCount + 1);
  };

  const handleRemoveStudent = async () => {
    const currentCount = status?.student_count ?? 0;
    await updateOccupancyLevel(Math.max(0, currentCount - 1));
  };

  const handleReset = async () => {
    await updateOccupancyLevel(0);
  };

  const controlModeLabel = useMemo(() => {
    if (!status) return 'Unknown';
    if (status.control_mode === 'MANUAL') return 'Manual';
    if (status.control_mode === 'AI_SIMULATION') return 'AI Simulation';
    return 'Edge AI (Not Connected)';
  }, [status]);

  const studentCount = status?.student_count ?? 0;
  const occupancyLevel = status?.occupancy_level ?? 'LOW';
  const acStatus = status?.ac_status ?? false;
  const temperature = status?.temperature ?? '—';

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <DashboardSection title="Simulator State">
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          <DashboardMetricCard title="Backend Health" value={health?.status === 'ok' ? 'Connected' : 'Offline'} subtitle="Live FastAPI connection" />
          <DashboardMetricCard title="Control Mode" value={controlModeLabel} subtitle="Reflects the backend control source" />
          <DashboardMetricCard title="Student Count" value={studentCount} subtitle="Current classroom occupancy" />
          <DashboardMetricCard title="Occupancy" value={occupancyLevel} subtitle="Current occupancy level" />
          <DashboardMetricCard title="AC" value={acStatus ? 'ON' : 'OFF'} subtitle="Current AC operating state" />
          <DashboardMetricCard title="Temperature" value={temperature} subtitle="Current target temperature" />
        </div>
        {error ? <div style={{ color: 'var(--danger)', marginTop: '0.75rem' }}>{error}</div> : null}
      </DashboardSection>

      <DashboardSection title="Classroom Simulation">
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          <div className="panel" style={{ padding: '1rem', background: 'var(--surface-elevated)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ margin: 0 }}>Classroom</h3>
              <div className="text-muted">{studentCount} students</div>
            </div>

            <div style={{ border: '1px solid var(--border)', borderRadius: '1rem', padding: '1rem', background: 'linear-gradient(135deg, var(--surface) 0%, var(--surface-elevated) 100%)' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                <div style={{ width: '90%', height: '12px', borderRadius: '999px', background: 'var(--border)', position: 'relative' }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                <div style={{ width: '78%', border: '2px solid var(--border)', borderRadius: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.03)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Wall-mounted AC</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: acStatus ? 'var(--success)' : 'var(--danger)' }} />
                      <div style={{ fontWeight: 700 }}>{acStatus ? 'ACTIVE' : 'OFF'}</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.5rem 0' }}>
                    <div style={{ width: '46px', height: '26px', borderRadius: '0.45rem', background: acStatus ? 'var(--accent)' : 'var(--border)', position: 'relative', overflow: 'hidden' }}>
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: acStatus ? 1 : 0.4 }}>
                        {acStatus ? (
                          <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                            <div style={{ position: 'absolute', left: '6px', top: '7px', width: '24px', height: '2px', background: 'white', animation: 'airflow 1.4s linear infinite' }} />
                            <div style={{ position: 'absolute', left: '6px', top: '12px', width: '20px', height: '2px', background: 'white', animation: 'airflow 1.4s linear infinite 0.4s' }} />
                          </div>
                        ) : null}
                      </div>
                    </div>
                    <div style={{ width: '12px', height: '22px', borderRadius: '999px', background: 'var(--border)' }} />
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(72px, 1fr))', justifyItems: 'center' }}>
                {Array.from({ length: Math.max(studentCount, 0) }).map((_, index) => (
                  <div key={index} style={{ display: 'grid', justifyItems: 'center', gap: '0.2rem' }}>
                    <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent) 0%, var(--border) 100%)', animation: 'studentPulse 2s ease-in-out infinite' }} />
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Student</div>
                  </div>
                ))}
                {studentCount === 0 ? <div className="text-muted" style={{ gridColumn: '1 / -1', textAlign: 'center' }}>No students currently in the room.</div> : null}
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gap: '0.75rem' }}>
            <div className="panel" style={{ padding: '1rem', background: 'var(--surface-elevated)' }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.75rem' }}>Student controls</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                <button type="button" onClick={handleAddStudent} disabled={busy}>Add Student</button>
                <button type="button" onClick={handleRemoveStudent} disabled={busy}>Remove Student</button>
                <button type="button" onClick={handleReset} disabled={busy}>Reset Classroom</button>
              </div>
            </div>

            <div className="panel" style={{ padding: '1rem', background: 'var(--surface-elevated)' }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.75rem' }}>Simulation controls</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                <button type="button" onClick={() => setAutoSimulation((value) => !value)}>{autoSimulation ? 'Pause Simulation' : 'Auto Simulation'}</button>
              </div>
            </div>

            <div className="panel" style={{ padding: '1rem', background: 'var(--surface-elevated)' }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Live state</h3>
              <div className="text-muted">Occupancy: {occupancyLevel}</div>
              <div className="text-muted">AC: {acStatus ? 'ON' : 'OFF'}</div>
              <div className="text-muted">Temperature: {temperature}</div>
            </div>
          </div>
        </div>
      </DashboardSection>

      <style>{`
        @keyframes airflow {
          from { transform: translateX(-8px); opacity: 0.4; }
          to { transform: translateX(16px); opacity: 1; }
        }
        @keyframes studentPulse {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-3px); }
        }
      `}</style>
    </div>
  );
}
