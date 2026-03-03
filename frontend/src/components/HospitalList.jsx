
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Building2, Phone, MapPin } from 'lucide-react';

const HospitalList = ({ district = 'Ernakulam' }) => {
    const [hospitals, setHospitals] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // API Call to get hospitals
        axios.get(`http://localhost:5000/api/hospitals?district=${district}`)
            .then(res => setHospitals(res.data))
            .catch(err => {
                console.error(err);
                setHospitals([]); // Should handle gracefully
            })
            .finally(() => setLoading(false));
    }, [district]);

    if (loading) return <div className="text-center text-slate-500 py-4">Finding nearby facilities...</div>;
    if (!hospitals.length) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Building2 className="text-red-500" /> Nearby Heart Care Facilities
            </h3>
            <p className="text-sm text-slate-500 mb-4">Based on your risk assessment, we recommend consulting a specialist.</p>

            <div className="space-y-3">
                {hospitals.map((hospital, index) => (
                    <div key={index} className="flex justify-between items-start border-b border-slate-50 pb-3 last:border-0 last:pb-0">
                        <div>
                            <h4 className="font-medium text-slate-800">{hospital.name}</h4>
                            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                                <MapPin size={12} /> {hospital.district}
                                <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-xs ml-2">{hospital.type || 'General'}</span>
                            </p>
                        </div>
                        <div className="text-right">
                            {hospital.contact && (
                                <a href={`tel:${hospital.contact}`} className="text-blue-600 hover:text-blue-800 text-sm flex items-center justify-end gap-1 font-medium transition-colors">
                                    <Phone size={12} /> Call
                                </a>
                            )}
                            <span className="text-xs text-slate-400 mt-1 block">Kerala</span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100 text-center">
                <a href="https://hospitals.spark.gov.in" target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline">
                    View all Government Hospitals (data.gov.in)
                </a>
            </div>
        </div>
    );
};

export default HospitalList;
