interface StatusCardProps {
  title: string;
  value: string | number | boolean | null;
  loading?: boolean;
  error?: string;
}

export function StatusCard({ title, value, loading, error }: StatusCardProps) {
  return (
    <section className="panel" style={{ padding: '1rem' }}>
      <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>{title}</h3>
      {loading ? (
        <p className="text-muted" style={{ margin: 0 }}>Loading...</p>
      ) : error ? (
        <p style={{ margin: 0, color: 'var(--danger)' }}>{error}</p>
      ) : (
        <p style={{ margin: 0, fontWeight: 600 }}>{String(value)}</p>
      )}
    </section>
  );
}
