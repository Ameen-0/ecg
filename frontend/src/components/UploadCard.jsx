
import React, { useState } from 'react';
import { Upload, X, FileImage, Camera } from 'lucide-react';

const UploadCard = ({ onUpload, isProcessing }) => {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreview(URL.createObjectURL(selectedFile));
        }
    };

    const clearFile = () => {
        setFile(null);
        setPreview(null);
    };

    const handleUploadClick = () => {
        if (file) {
            onUpload(file);
        }
    };

    return (
        <div className="card space-y-4">
            <h3 className="text-xl font-extrabold text-slate-800 flex items-center gap-2 uppercase tracking-tight">
                <FileImage className="text-blue-500" size={20} /> Scan ECG Image
            </h3>
            <p className="text-[11px] text-slate-500 font-medium leading-relaxed uppercase tracking-tighter">
                Upload a photo or take a picture of your paper ECG. For best results, make sure the grid lines are visible.
            </p>

            {!preview ? (
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-blue-400 transition-all cursor-pointer relative group bg-slate-50/50">
                    <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                        disabled={isProcessing}
                    />
                    <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                        <div className="p-4 bg-white rounded-full shadow-sm group-hover:scale-110 transition-transform">
                            <Upload className="text-blue-500" size={24} />
                        </div>
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-widest">Select Image Asset</p>
                    </div>
                </div>
            ) : (
                <div className="relative rounded-xl overflow-hidden border border-slate-200 shadow-sm group aspect-video bg-slate-100">
                    <img src={preview} alt="ECG Preview" className="w-full h-full object-contain" />
                    <button
                        onClick={clearFile}
                        className="absolute top-2 right-2 bg-white/90 p-2 rounded-full shadow-md hover:bg-white text-slate-700 transition-colors disabled:opacity-50"
                        disabled={isProcessing}
                    >
                        <X size={16} />
                    </button>
                    {isProcessing && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] flex items-center justify-center">
                            <span className="text-[10px] font-bold text-blue-900 bg-blue-100 px-4 py-2 rounded-full shadow-sm animate-pulse uppercase tracking-[0.2em]">Digitizing...</span>
                        </div>
                    )}
                </div>
            )}

            <div className="md:hidden">
                <label className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-slate-100 text-slate-700 rounded-xl cursor-pointer hover:bg-slate-200 transition-colors border border-slate-200 shadow-sm">
                    <Camera size={18} />
                    <span className="text-xs font-bold uppercase tracking-widest">Camera Input</span>
                    <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleFileChange}
                        className="hidden"
                        disabled={isProcessing}
                    />
                </label>
            </div>

            <button
                onClick={handleUploadClick}
                disabled={!file || isProcessing}
                className={`w-full py-4 px-4 rounded-xl font-bold shadow-lg transition-all uppercase tracking-[0.2em] text-[10px]
          ${!file || isProcessing
                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                        : 'bg-slate-800 text-white hover:bg-slate-900 active:scale-[0.98]'
                    }
        `}
            >
                {isProcessing ? 'Analyzing...' : 'Start AI Analysis'}
            </button>
        </div>
    );
};

export default UploadCard;
