
import React, { useState } from 'react';
import WaveformChart from './WaveformChart';
import HospitalList from './HospitalList';
import { Download, AlertTriangle, CheckCircle, Activity, HeartPulse, Brain, Info } from 'lucide-react';
import axios from 'axios';

const ResultsSection = ({ results, aqi, showHospitals, district }) => {

    const {
        heart_rate_desc,
        heart_rate_range,
        autonomic_indicator,
        pattern_alert,
        confidence_score,
        signal_quality,
        signal,
        filename
    } = results || {};

    const [downloading, setDownloading] = useState(false);

    const handleDownloadPDF = async () => {
        setDownloading(true);
        try {
            const response = await axios.post('http://localhost:5000/api/report', results);
            const { url } = response.data;
            if (url) {
                const link = document.createElement('a');
                link.href = `http://localhost:5000${url}`;
                link.setAttribute('download', `ECG_Digitized_${filename || 'Scan'}.pdf`);
                document.body.appendChild(link);
                link.click();
                link.remove();
            }
        } catch (error) {
            console.error("PDF Generation failed", error);
            alert("Failed to generate digital report.");
        } finally {
            setDownloading(false);
        }
    };


    let alertColor = 'text-slate-600 bg-slate-50 border-slate-200';
    if (pattern_alert?.includes('Marked')) alertColor = 'text-amber-600 bg-amber-50 border-amber-200';
    else if (pattern_alert?.includes('Mild')) alertColor = 'text-blue-600 bg-blue-50 border-blue-200';

    const qualityColor = signal_quality > 80 ? 'text-emerald-600' : signal_quality > 60 ? 'text-slate-600' : 'text-amber-600';

    const isLowConfidence = confidence_score < 70;
    const isRhythmUnreliable = confidence_score < 85;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Mandatory Academic Disclaimer */}
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-xl flex gap-3 items-start">
                <Info className="text-blue-500 shrink-0 mt-0.5" size={18} />
                <p className="text-xs text-blue-800 leading-relaxed font-medium">
                    CardioAware performs AI-based pattern analysis on ECG images for educational and research
                    use only. It does NOT provide medical diagnosis or clinical measurements.
                    Calculated values are estimates derived from visual image contrast.
                </p>
            </div>

            {/* Metrics Dashboard */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className={`card text-center ${isRhythmUnreliable ? 'opacity-60 grayscale' : ''}`}>
                    <HeartPulse className="mx-auto text-slate-500 mb-2" size={24} />
                    <div className="text-xs font-bold text-slate-800 uppercase tracking-tight leading-tight">
                        {heart_rate_desc} – Rhythm Speed
                    </div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mt-2">
                        {isRhythmUnreliable ? 'Unreliable Data' : `Estimated BPM: ${heart_rate_range}`}
                    </div>
                </div>

                <div className="card text-center">
                    <Brain className="mx-auto text-slate-500 mb-2" size={24} />
                    <div className="text-sm font-bold text-slate-800 leading-tight">{autonomic_indicator}</div>
                    <div className="text-[10px] text-slate-600 font-bold mt-1">Variability Score: {results?.hrv} ms</div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mt-2 tracking-tighter">AI Body Rhythm Index</div>
                </div>

                <div className={`card text-center border-l-4 ${alertColor.split(' ')[2].replace('border', 'border-l')}`}>
                    <Activity className="mx-auto text-slate-500 mb-2" size={24} />
                    <div className={`text-xs font-bold leading-tight ${alertColor.split(' ')[0]}`}>{pattern_alert}</div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mt-2">Overall Scan Result</div>
                </div>

                <div className="card text-center">
                    <div className={`text-3xl font-bold ${qualityColor}`}>{signal_quality}</div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mt-1">Scan Clarity Score</div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                        <div className="h-1.5 rounded-full bg-slate-400" style={{ width: `${signal_quality}%` }}></div>
                    </div>
                </div>
            </div>

            {/* Waveform Visualization */}
            <div className="card relative p-0 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                    <h4 className="text-sm font-bold text-slate-700">AI-Extracted Signal Representation (Non-Diagnostic)</h4>
                    <p className="text-[10px] text-slate-500 italic">Derived from image contrast and geometry; not electrical ECG voltage.</p>
                </div>
                <div className="p-4">
                    <WaveformChart signal={signal} />
                </div>

                {isLowConfidence && (
                    <div className="absolute inset-0 bg-white/70 backdrop-blur-md flex items-center justify-center p-6">
                        <div className="text-center max-w-xs">
                            <AlertTriangle className="mx-auto text-amber-500 mb-2" size={32} />
                            <h4 className="font-bold text-slate-800 uppercase text-sm">Signal Under Processing Threshold</h4>
                            <p className="text-xs text-slate-600 mt-1">Extraction confidence is too low. Please provide a higher resolution scan with visible grid lines.</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Research Interpretation */}
            <div className={`card ${alertColor}`}>
                <h4 className="font-bold text-sm mb-3 flex items-center gap-2 uppercase tracking-wide">
                    {pattern_alert?.includes('No Significant') ? <CheckCircle size={18} className="text-slate-600" /> : <AlertTriangle size={18} className="text-amber-600" />}
                    AI Scan Summary
                </h4>
                <p className="text-slate-700 text-sm leading-relaxed mb-6">
                    {pattern_alert?.includes('No Significant')
                        ? "The scan shows a steady and consistent rhythm."
                        : "The AI found some irregular gaps in this rhythm. This is a pattern observation only and not a medical finding."}
                    <br />
                    <span className="text-xs italic text-slate-500 block mt-3">
                        {aqi && aqi.level !== 'Good' && dp_aqi_warning(aqi)}
                    </span>
                </p>

                <div className="flex flex-col md:flex-row gap-4">
                    <button
                        onClick={handleDownloadPDF}
                        disabled={downloading}
                        className="w-full btn-primary flex items-center justify-center gap-2 text-xs bg-slate-800 hover:bg-slate-900 py-3"
                    >
                        {downloading ? 'Processing Digital Export...' : <><Download size={16} /> Export Digitized Pattern (PDF)</>}
                    </button>
                </div>
            </div>

            {/* Hospitals (Conditional) */}
            {showHospitals && (
                <div className="animate-fade-in">
                    <HospitalList district={district || 'Ernakulam'} />
                </div>
            )}
        </div>
    );
};

const dp_aqi_warning = (aqi) => {
    return `Environmental Context: External AQI in ${aqi.city} is currently '${aqi.level}'.`;
}

export default ResultsSection;
