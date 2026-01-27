import React, { useState } from 'react';
import { X, UserPlus, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function EmployeeRegistrationModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    epc_code: '',
    full_name: '',
    office: '',
    position: '',
    address: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.epc_code.trim() || !formData.full_name.trim()) {
      setError('EPC Code and Full Name are required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8766/api/employees/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to register employee');
      }

      setSuccess(true);
      setTimeout(() => {
        onSuccess && onSuccess(result.employee);
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-lg max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-gradient-to-r from-cyan-500 to-purple-500 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <UserPlus className="w-6 h-6 text-white" />
            <h2 className="text-xl font-bold text-white">Register New Employee</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-xl transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* EPC Code */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              EPC Code <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              name="epc_code"
              value={formData.epc_code}
              onChange={handleChange}
              placeholder="E280119120006D655D46033C"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
              disabled={loading || success}
              required
            />
            <p className="mt-1 text-xs text-slate-400">24-character RFID tag code</p>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Full Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="John Doe"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
              disabled={loading || success}
              required
            />
          </div>

          {/* Office */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Office
            </label>
            <input
              type="text"
              name="office"
              value={formData.office}
              onChange={handleChange}
              placeholder="Main Office"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
              disabled={loading || success}
            />
          </div>

          {/* Position */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Position
            </label>
            <input
              type="text"
              name="position"
              value={formData.position}
              onChange={handleChange}
              placeholder="Software Engineer"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
              disabled={loading || success}
            />
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Address
            </label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="City, Province"
              rows="2"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all resize-none"
              disabled={loading || success}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <p className="text-sm text-rose-400">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="flex items-center gap-2 px-4 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <p className="text-sm text-emerald-400">Employee registered successfully!</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-slate-700/50 hover:bg-slate-700 text-white rounded-xl font-medium transition-colors"
              disabled={loading || success}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              disabled={loading || success}
            >
              {loading ? 'Registering...' : success ? 'Registered!' : 'Register Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
