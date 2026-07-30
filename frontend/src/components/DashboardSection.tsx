interface DashboardSectionProps {
  title: string;
  children: React.ReactNode;
}

export function DashboardSection({ title, children }: DashboardSectionProps) {
  return (
    <section className="panel" style={{ padding: '1rem' }}>
      <h3 style={{ marginTop: 0, marginBottom: '0.75rem' }}>{title}</h3>
      {children}
    </section>
  );
}
