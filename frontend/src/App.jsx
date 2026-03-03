
import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import UploadCard from './components/UploadCard';
import ResultsSection from './components/ResultsSection';
import AQICard from './components/AQICard';
import axios from 'axios';
import { Loader2, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [aqi, setAqi] = useState(null);
  const [error, setError] = useState(null);
  const [showHospitals, setShowHospitals] = useState(false);
  const [location, setLocation] = useState('Kochi');

  const KERALA_LOCATIONS = [
    'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
    'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
    'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod'
  ];

  useEffect(() => {
    axios.get(`${API_BASE}/aqi?city=${location}`)
      .then(res => setAqi(res.data))
      .catch(err => console.error("Failed to fetch AQI", err));
  }, [location]);

  const handleUpload = async (file) => {
    setFile(file);
    setLoading(true);
    setError(null);
    setResults(null);
    setShowHospitals(false);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const data = response.data;
      setResults(data);

      if (['Mild', 'Marked'].some(key => data.pattern_alert?.includes(key))) {
        setShowHospitals(true);
      }
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred during digitization.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-8 space-y-8">

        {!results && !loading && (
          <div className="max-w-4xl mx-auto space-y-4 mb-8">
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-800 tracking-tight leading-tight">
              ECG Rhythm <span className="text-blue-600">Scanner</span>
            </h2>
            <p className="text-sm md:text-lg text-slate-500 font-medium max-w-2xl leading-relaxed">
              Turn your paper ECG photos into digital signals. View rhythm patterns and AI insights using image-based digitization.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div id="upload" className="lg:col-span-1 space-y-6">
            <UploadCard onUpload={handleUpload} isProcessing={loading} />

            <div id="aqi" className="card bg-white/50 border-none shadow-none">
              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Environment Context</label>
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full p-3 border border-slate-200 rounded-xl mb-4 text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white transition-all shadow-sm"
              >
                {KERALA_LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
              </select>
              {aqi && <AQICard data={aqi} />}
            </div>

            <div className="card bg-slate-100 border-none shadow-none">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="mt-0.5 flex-shrink-0 text-slate-400" />
                <div className="text-[11px] text-slate-500 leading-relaxed italic font-medium">
                  <strong>Academic Research Tool:</strong> This system is for educational
                  demonstration purposes only. It performs pattern analysis on IMAGE data
                  and does not provide clinical measurements or medical advice.
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            {loading && (
              <div className="card flex flex-col items-center justify-center p-12 min-h-[400px]">
                <Loader2 className="animate-spin text-blue-500 mb-6" size={48} />
                <p className="text-lg font-bold text-slate-700 uppercase tracking-widest">Digitization in Progress</p>
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter mt-1">Extracting Rhythm Characteristics...</p>
              </div>
            )}

            {error && (
              <div className="bg-rose-50 border border-rose-100 text-rose-700 p-4 rounded-xl flex items-center gap-3">
                <AlertCircle size={20} className="shrink-0" />
                <span className="text-sm font-semibold uppercase tracking-tight">{error}</span>
              </div>
            )}

            {results && !loading && (
              <div id="hospitals">
                <ResultsSection
                  results={results}
                  aqi={aqi}
                  showHospitals={showHospitals}
                  district={location}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-8 mt-12 bg-slate-50/50">
        <div className="container mx-auto px-4 text-center">
          <p className="text-[11px] text-slate-400 font-bold uppercase tracking-[0.2em]">CardioAware Academic Pilot</p>
          <p className="text-[10px] text-slate-300 mt-2 italic font-medium">Non-Clinical Educational Research. KTU Final Year Project.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
