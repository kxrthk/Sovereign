import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { TerminalSquare } from 'lucide-react';

export default function CortexLog() {
    const [logs, setLogs] = useState<string>('System Online. Awaiting logs...');
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await axios.get('/api/cortex_log');
                if (res.data.log_text) {
                    setLogs(res.data.log_text);
                }
            } catch (e) {
                console.error('Cortex log fetch error', e);
            }
        };

        fetchLogs();
        const inv = setInterval(fetchLogs, 5000);

        return () => clearInterval(inv);
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--text-primary)', letterSpacing: '2px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TerminalSquare size={20} className="neon-purple" /> CORTEX NEURAL LOGS
            </h2>
            <div className="glass-panel crt-effect" style={{ flex: 1, padding: '24px', background: 'rgba(0, 0, 0, 0.6)', border: '1px solid var(--border-glow-purple)', overflowY: 'auto' }}>
                <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                    {logs}
                </pre>
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
