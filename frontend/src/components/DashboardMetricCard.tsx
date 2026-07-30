interface DashboardMetricCardProps {
  title: string;
  value: string | number | boolean | null;
  subtitle?: string;
}

export function DashboardMetricCard({ title, value, subtitle }: DashboardMetricCardProps) {
  return (
    <div className="panel" style={{ padding: '1rem' }}>
      <div className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '0.35rem' }}>{title}</div>
      <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{String(value)}</div>
      {subtitle ? <div className="text-muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>{subtitle}</div> : null}
    </div>
  );
}
