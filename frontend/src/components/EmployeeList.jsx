import React, { useState, useEffect } from 'react';
import { Users, Search, Briefcase, MapPin, UserPlus } from 'lucide-react';
import { getEmployees } from '../lib/supabase';
import EmployeeRegistrationModal from './EmployeeRegistrationModal';

export default function EmployeeList() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  useEffect(() => {
    loadEmployees();
  }, []);

  async function loadEmployees() {
    try {
      const data = await getEmployees();
      setEmployees(data || []);
    } catch (error) {
      console.error('Failed to load employees:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleRegisterSuccess(newEmployee) {
    // Reload employees list
    loadEmployees();
  }

  const filteredEmployees = employees.filter(emp => {
    const searchLower = search.toLowerCase();
    return (
      emp.full_name?.toLowerCase().includes(searchLower) ||
      emp.office?.toLowerCase().includes(searchLower) ||
      emp.position?.toLowerCase().includes(searchLower) ||
      emp.epc_code?.toLowerCase().includes(searchLower)
    );
  });

  if (loading) {
    return (
      <div className="glass-card p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-slate-400">Loading employees...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {showRegisterModal && (
        <EmployeeRegistrationModal
          onClose={() => setShowRegisterModal(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}

      <div className="glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/50">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold text-white">Registered Employees</h3>
              <p className="text-sm text-slate-400">{employees.length} employees with RFID cards</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowRegisterModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 rounded-xl font-medium text-white shadow-lg hover:scale-105 transition-all"
              >
                <UserPlus className="w-4 h-4" />
                <span className="hidden sm:inline">Register Employee</span>
                <span className="sm:hidden">Register</span>
              </button>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search employees..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 pr-4 py-2 bg-slate-800/50 border border-slate-600 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          {filteredEmployees.length === 0 ? (
            <div className="col-span-full text-center py-8 text-slate-400">
              <Users className="w-14 h-14 mx-auto mb-4 text-slate-600" />
              <p className="font-medium text-slate-300">No employees found</p>
              <p className="text-sm mt-1">
                {search ? 'Try a different search term' : 'Add employees to the database'}
              </p>
            </div>
          ) : (
            filteredEmployees.map((emp) => (
              <div
                key={emp.id}
                className="glass-card-dark p-4 hover:scale-105 transition-all cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center text-white font-semibold text-lg shadow-lg">
                      {emp.full_name?.charAt(0) || '?'}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-white truncate">
                      {emp.full_name}
                    </h4>
                    <div className="flex items-center gap-1 text-sm text-slate-400 mt-1">
                      <Briefcase className="w-3.5 h-3.5" />
                      <span className="truncate">{emp.position || 'No position'}</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-slate-400 mt-0.5">
                      <MapPin className="w-3.5 h-3.5" />
                      <span className="truncate">{emp.office || 'No office'}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-700/50">
                  <p className="text-xs text-slate-500 font-mono truncate">
                    EPC: {emp.epc_code}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
