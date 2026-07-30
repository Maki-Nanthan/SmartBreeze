import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { DashboardMetricCard } from '../components/DashboardMetricCard';
import { DashboardSection } from '../components/DashboardSection';
import { fetchAcEvents, fetchHealth, fetchOccupancyHistory, fetchRunningTime, fetchStatus, postManualControl, postOccupancy } from '../services/dashboardApi';
import { ClassroomStatusResponse, HealthResponse } from '../types/api';
import { ACEventEntry, OccupancyHistoryEntry, RunningTimeResponse } from '../types/dashboard';
import { edgeAiAdapter } from '../services/edgeAiAdapter';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<ClassroomStatusResponse | null>(null);
  const [history, setHistory] = useState<OccupancyHistoryEntry[]>([]);
  const [events, setEvents] = useState<ACEventEntry[]>([]);
  const [runningTime, setRunningTime] = useState<RunningTimeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [studentCount, setStudentCount] = useState<number>(0);
  const [acStatus, setAcStatus] = useState<string>('OFF');
  const [temperature, setTemperature] = useState('22');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoStatus, setVideoStatus] = useState('Waiting for upload');
  const [videoPlaying, setVideoPlaying] = useState(false);
  const [cameraStatus, setCameraStatus] = useState('Camera idle');
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const uploadVideoRef = useRef<HTMLVideoElement | null>(null);
  const webcamVideoRef = useRef<HTMLVideoElement | null>(null);

  const loadData = async () => {
    try {
      const [healthResponse, statusResponse, historyResponse, eventsResponse, runningTimeResponse] = await Promise.all([
        fetchHealth(),
        fetchStatus(),
        fetchOccupancyHistory(),
        fetchAcEvents(),
        fetchRunningTime(),
      ]);

      setHealth(healthResponse);
      setStatus(statusResponse);
      setHistory(historyResponse);
      setEvents(eventsResponse);
      setRunningTime(runningTimeResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard data');
    } finally {
      setLoading(false);
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
    if (status) {
      setStudentCount(status.student_count ?? 0);
      setAcStatus(status.ac_status ? 'ON' : 'OFF');
      setTemperature(status.temperature != null ? String(status.temperature) : '22');
    }
  }, [status]);

  const controlModeLabel = useMemo(() => {
    if (!status) return 'Unknown';
    if (status.control_mode === 'AI_SIMULATION') return 'AI Simulation';
    if (status.control_mode === 'MANUAL') return 'Manual';
    if (status.control_mode === 'EDGE_AI') return 'Edge AI';
    return 'Edge AI (Not Connected)';
  }, [status]);

  useEffect(() => {
    return () => {
      if (videoPreviewUrl) {
        URL.revokeObjectURL(videoPreviewUrl);
      }
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream, videoPreviewUrl]);

  const handleManualSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      const nextStatus = await postManualControl({
        student_count: studentCount,
        ac_status: acStatus === 'ON',
        temperature: Number(temperature),
      });
      setStatus(nextStatus);
      setError(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to apply manual control');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVideoUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'];
    if (!allowedTypes.includes(file.type)) {
      setVideoError('Please upload a supported video file: MP4, WebM, Ogg, or MOV.');
      setVideoFile(null);
      setVideoPreviewUrl(null);
      return;
    }

    if (videoPreviewUrl) {
      URL.revokeObjectURL(videoPreviewUrl);
    }

    const previewUrl = URL.createObjectURL(file);
    setVideoFile(file);
    setVideoPreviewUrl(previewUrl);
    setVideoError(null);
    setVideoStatus('Video uploaded. Ready for AI Simulation Mode.');
    setVideoPlaying(false);
  };

  const handleVideoPlayback = async () => {
    if (!uploadVideoRef.current || !videoFile) return;

    if (uploadVideoRef.current.paused) {
      await uploadVideoRef.current.play();
      setVideoPlaying(true);
      setVideoStatus('Playing video in AI Simulation Mode');
    } else {
      uploadVideoRef.current.pause();
      setVideoPlaying(false);
      setVideoStatus('Video paused');
    }
  };

  useEffect(() => {
    if (!uploadVideoRef.current || !videoFile || !videoPlaying) return;

    const syncSimulation = async () => {
      if (!uploadVideoRef.current) return;
      try {
        const level = await edgeAiAdapter.predictOccupancy(uploadVideoRef.current);
        const nextStatus = await postOccupancy({ occupancy_level: level });
        setStatus(nextStatus);
      } catch (err) {
        setVideoError('Unable to perform Edge AI video inference or update backend');
      }
    };

    const interval = window.setInterval(() => {
      void syncSimulation();
    }, 1000);
    return () => window.clearInterval(interval);
  }, [videoFile, videoPlaying]);

  useEffect(() => {
    if (!cameraActive || !webcamVideoRef.current || !cameraStream) return;

    webcamVideoRef.current.srcObject = cameraStream;
    void webcamVideoRef.current.play().catch(() => {
      setCameraStatus('Camera stream ready but playback was blocked');
    });

    const syncSimulation = async () => {
      if (!webcamVideoRef.current) return;
      try {
        const level = await edgeAiAdapter.predictOccupancy(webcamVideoRef.current);
        const nextStatus = await postOccupancy({ occupancy_level: level });
        setStatus(nextStatus);
      } catch (err) {
        setVideoError('Unable to perform Edge AI webcam inference or update backend');
      }
    };

    const interval = window.setInterval(() => {
      void syncSimulation();
    }, 1000);
    setCameraStatus('Camera running in Edge AI Mode');
    return () => window.clearInterval(interval);
  }, [cameraActive, cameraStream]);

  const startCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setVideoError('Camera access is not supported in this browser.');
      setCameraStatus('Camera unavailable');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      setCameraStream(stream);
      setCameraActive(true);
      setVideoStatus('Camera started. AI Simulation Mode is active.');
      setVideoError(null);
    } catch {
      setCameraStatus('Camera permission denied');
      setVideoError('Please allow camera access to start webcam mode.');
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
    setCameraStream(null);
    setCameraActive(false);
    setCameraStatus('Camera stopped');
    setVideoStatus('Webcam stopped');
  };

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <DashboardSection title="System Overview">
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))' }}>
          <DashboardMetricCard title="Backend Health" value={health?.status === 'ok' ? 'Connected' : 'Offline'} subtitle="Live FastAPI connection" />
          <DashboardMetricCard title="Current Occupancy" value={status?.occupancy_level ?? '—'} subtitle="Derived by the backend" />
          <DashboardMetricCard title="Student Count" value={status?.student_count ?? 0} subtitle="AI Model Prediction" />
          <DashboardMetricCard title="AC Status" value={status?.ac_status ? 'ON' : 'OFF'} subtitle="Current backend state" />
          <DashboardMetricCard title="Temperature" value={status?.temperature ?? '—'} subtitle="Current AC target temperature" />
          <DashboardMetricCard title="Control Mode" value={controlModeLabel} subtitle="Simulation or manual control" />
          <DashboardMetricCard title="Total AC Running Time" value={runningTime ? `${runningTime.total_minutes.toFixed(1)} min` : '—'} subtitle="Calculated from stored AC events" />
          <DashboardMetricCard title="Last Updated" value={status ? new Date(status.timestamp).toLocaleString() : '—'} subtitle="Backend timestamp" />
        </div>
      </DashboardSection>

      <DashboardSection title="Video & Webcam Simulation Mode">
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          <div className="panel-muted" style={{ padding: '1rem' }}>
            <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Upload video</h3>
            <p className="text-muted" style={{ marginTop: 0, marginBottom: '0.75rem' }}>AI Simulation Mode — the real Edge AI model is not integrated yet.</p>
            <input type="file" accept="video/mp4,video/webm,video/ogg,video/quicktime" onChange={handleVideoUpload} />
            {videoError ? <div style={{ color: 'var(--danger)', marginTop: '0.75rem' }}>{videoError}</div> : null}
            {videoPreviewUrl ? (
              <div style={{ marginTop: '0.75rem' }}>
                <video ref={uploadVideoRef} src={videoPreviewUrl} controls={false} style={{ width: '100%', borderRadius: '0.75rem', background: 'black' }} />
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                  <button type="button" onClick={handleVideoPlayback}>{videoPlaying ? 'Pause' : 'Play'}</button>
                </div>
              </div>
            ) : null}
            <div className="text-muted" style={{ marginTop: '0.75rem' }}>{videoStatus}</div>
          </div>

          <div className="panel-muted" style={{ padding: '1rem' }}>
            <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Webcam mode</h3>
            <p className="text-muted" style={{ marginTop: 0, marginBottom: '0.75rem' }}>The webcam stream is prepared for future Edge AI integration; current behavior is simulation-only.</p>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button type="button" onClick={startCamera} disabled={cameraActive}>Start webcam</button>
              <button type="button" onClick={stopCamera} disabled={!cameraActive}>Stop webcam</button>
            </div>
            <video ref={webcamVideoRef} autoPlay playsInline muted style={{ width: '100%', borderRadius: '0.75rem', background: 'black', display: cameraActive ? 'block' : 'none' }} />
            {!cameraActive ? <div className="text-muted" style={{ marginTop: '0.5rem' }}>Camera status: {cameraStatus}</div> : null}
            {cameraActive ? <div className="text-muted" style={{ marginTop: '0.5rem' }}>{cameraStatus}</div> : null}
          </div>


        </div>
      </DashboardSection>

      <DashboardSection title="Manual Control">
        <form onSubmit={handleManualSubmit} style={{ display: 'grid', gap: '0.75rem' }}>
          <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
            <label style={{ display: 'grid', gap: '0.25rem' }}>
              <span className="text-muted">Student count</span>
              <input type="number" min="0" max="100" value={studentCount} onChange={(event) => setStudentCount(Number(event.target.value))} />
            </label>
            <label style={{ display: 'grid', gap: '0.25rem' }}>
              <span className="text-muted">AC</span>
              <select value={acStatus} onChange={(event) => setAcStatus(event.target.value)}>
                <option value="ON">ON</option>
                <option value="OFF">OFF</option>
              </select>
            </label>
            <label style={{ display: 'grid', gap: '0.25rem' }}>
              <span className="text-muted">Temperature</span>
              <input type="number" min="16" max="35" step="0.5" value={temperature} onChange={(event) => setTemperature(event.target.value)} />
            </label>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button type="submit" disabled={submitting}>
              {submitting ? 'Applying...' : 'Apply Manual Control'}
            </button>
            <span className="text-muted">Control Mode: Manual</span>
          </div>
          {error ? <div style={{ color: 'var(--danger)' }}>{error}</div> : null}
        </form>
      </DashboardSection>

      <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        <DashboardSection title="Occupancy History">
          {loading ? (
            <div className="text-muted">Loading history...</div>
          ) : error ? (
            <div style={{ color: 'var(--danger)' }}>{error}</div>
          ) : history.length === 0 ? (
            <div className="text-muted">No occupancy history yet.</div>
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {history.map((item) => (
                <div key={item.id} className="panel-muted" style={{ padding: '0.75rem' }}>
                  <div style={{ fontWeight: 600 }}>{item.occupancy_level}</div>
                  <div className="text-muted" style={{ fontSize: '0.9rem' }}>{new Date(item.timestamp).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </DashboardSection>

        <DashboardSection title="AC State Changes">
          {loading ? (
            <div className="text-muted">Loading events...</div>
          ) : error ? (
            <div style={{ color: 'var(--danger)' }}>{error}</div>
          ) : events.length === 0 ? (
            <div className="text-muted">No AC events available.</div>
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {events.map((event) => (
                <div key={event.id} className="panel-muted" style={{ padding: '0.75rem' }}>
                  <div style={{ fontWeight: 600 }}>{event.ac_status ? 'AC ON' : 'AC OFF'} • {event.temperature ?? '—'}°C</div>
                  <div className="text-muted" style={{ fontSize: '0.9rem' }}>{event.reason ?? 'No reason provided'}</div>
                  <div className="text-muted" style={{ fontSize: '0.9rem' }}>{new Date(event.timestamp).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </DashboardSection>
      </div>

      <DashboardSection title="Occupancy Timeline">
        {loading ? (
          <div className="text-muted">Loading timeline...</div>
        ) : error ? (
          <div style={{ color: 'var(--danger)' }}>{error}</div>
        ) : history.length === 0 ? (
          <div className="text-muted">No timeline data yet.</div>
        ) : (
          <div style={{ height: 300, width: '100%', marginTop: '1rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={[...history].reverse()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="timestamp" tickFormatter={(tick) => new Date(tick).toLocaleTimeString()} stroke="#888" />
                <YAxis stroke="#888" />
                <Tooltip 
                  labelFormatter={(label) => {
                    if (typeof label === 'string' || typeof label === 'number') {
                      return new Date(label).toLocaleString();
                    }
                    return '';
                  }}
                  contentStyle={{ backgroundColor: '#1a1a1a', border: 'none', borderRadius: '8px' }}
                />
                <Line type="stepAfter" dataKey="student_count" stroke="#646cff" strokeWidth={2} name="Student Count" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </DashboardSection>
    </div>
  );
}
