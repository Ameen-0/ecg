
import React from 'react';
import { Cloud, MapPin } from 'lucide-react';

const AQICard = ({ data }) => {
    if (!data || !data.aqi) return null;

    const { aqi, level, description, city, station } = data;

    // Premium Color Logic (Slate-friendly intensities)
    let colorClass = 'text-emerald-700 bg-emerald-50 border-emerald-100';
    if (aqi > 50) colorClass = 'text-amber-700 bg-amber-50 border-amber-100';
    if (aqi > 100) colorClass = 'text-orange-700 bg-orange-50 border-orange-100';
    if (aqi > 150) colorClass = 'text-rose-700 bg-rose-50 border-rose-100';

    return (
        <div className="card">
            <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                    <Cloud size={20} className="text-blue-500" />
                    Local Air Quality
                </h3>
                <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-tight">STATION</span>
                    <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
                        <MapPin size={10} /> {station || city}
                    </span>
                </div>
            </div>

            <div className={`p-5 rounded-2xl border ${colorClass} mb-4 flex items-center justify-between shadow-sm`}>
                <div>
                    <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">Status</span>
                    <div className="text-xl font-bold leading-tight">{level}</div>
                </div>
                <div className="text-right">
                    <span className="text-[10px] uppercase tracking-widest font-bold opacity-60">AQI Index</span>
                    <div className="text-3xl font-black">{aqi}</div>
                </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed font-medium opacity-80 italic">
                "{description}"
            </p>
        </div>
    );
};

export default AQICard;
