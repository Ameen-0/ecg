
import React from 'react';
import { Heart, Activity, MapPin, CloudSun } from 'lucide-react';

const Header = () => {
    return (
        <header className="glass shadow-sm sticky top-0 z-50 border-b border-white/20">
            <div className="container mx-auto px-4 py-3 flex justify-between items-center">
                <div className="flex items-center space-x-2">
                    <div className="bg-red-50 p-2 rounded-full">
                        <Heart className="text-red-500 fill-current" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-extrabold text-slate-800 tracking-tight leading-none">CardioAware</h2>
                        <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mt-1">AI Body Rhythm Scanner</p>
                    </div>
                </div>

                <nav className="hidden md:flex items-center space-x-8">
                    <a href="#upload" className="flex items-center space-x-2 text-slate-600 hover:text-blue-600 transition-colors">
                        <Activity size={16} />
                        <span className="text-xs font-bold uppercase tracking-widest">Scan ECG</span>
                    </a>
                    <a href="#aqi" className="flex items-center space-x-2 text-slate-600 hover:text-emerald-600 transition-colors">
                        <CloudSun size={16} />
                        <span className="text-xs font-bold uppercase tracking-widest">AQI Check</span>
                    </a>
                    <a href="#hospitals" className="flex items-center space-x-2 text-slate-600 hover:text-rose-600 transition-colors">
                        <MapPin size={16} />
                        <span className="text-xs font-bold uppercase tracking-widest">Find Care</span>
                    </a>
                </nav>
            </div>
        </header>
    );
};

export default Header;
