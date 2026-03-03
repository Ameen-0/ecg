
import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const WaveformChart = ({ signal, samplingRate = 100 }) => {
    const [mounted, setMounted] = React.useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    const data = useMemo(() => {
        if (!Array.isArray(signal)) return [];
        const step = Math.max(1, Math.floor(signal.length / 500));
        return signal.filter((_, i) => i % step === 0).map((value, index) => ({
            time: (index * step) / samplingRate,
            value: value
        }));
    }, [signal, samplingRate]);

    if (!mounted) return <div className="h-[300px] w-full bg-slate-50 animate-pulse rounded-lg" />;

    return (
        <div className="w-full bg-white rounded-lg p-4 border border-slate-100 shadow-sm relative overflow-hidden">
            <h4 className="text-sm font-semibold text-slate-500 mb-2">AI-Extracted ECG Waveform</h4>
            <div className="h-[300px] w-full min-h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis
                            dataKey="time"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            tickFormatter={(val) => `${val.toFixed(1)}s`}
                            stroke="#94a3b8"
                            fontSize={12}
                        />
                        <YAxis hide domain={['auto', 'auto']} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '4px' }}
                            itemStyle={{ color: '#0ea5e9' }}
                            labelFormatter={(label) => `Time: ${label.toFixed(2)}s`}
                            formatter={(value) => [value.toFixed(2), 'Amplitude']}
                        />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#ef4444"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4 }}
                            animationDuration={1000}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default WaveformChart;
