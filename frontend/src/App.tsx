import React, { useState, useEffect } from 'react';
import { 
  CandidateProfile, 
  DiscoveredJob, 
  ApplicationStats, 
  ApplicationRecord, 
  ApplicationPreview 
} from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'jobs' | 'profile' | 'applications' | 'agents'>('dashboard');
  const [candidate, setCandidate] = useState<CandidateProfile | null>(null);
  const [jobs, setJobs] = useState<DiscoveredJob[]>([]);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [stats, setStats] = useState<ApplicationStats>({
    total_applications: 0,
    awaiting_approval: 0,
    submitted: 0,
    confirmed: 0,
    interviews: 0,
    assessments: 0,
    offers: 0,
    rejections: 0,
  });
  const [activePreview, setActivePreview] = useState<ApplicationPreview | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const candRes = await fetch('/api/v1/candidate/profile');
      if (candRes.ok) {
        const cData = await candRes.json();
        setCandidate(cData);

        // Fetch jobs & stats
        const jobsRes = await fetch('/api/v1/jobs?limit=50');
        if (jobsRes.ok) {
          const jData = await jobsRes.json();
          setJobs(jData);
        }

        const statsRes = await fetch(`/api/v1/applications/stats?candidate_id=${cData.id}`);
        if (statsRes.ok) {
          const sData = await statsRes.json();
          setStats(sData);
        }

        const appsRes = await fetch(`/api/v1/applications?candidate_id=${cData.id}`);
        if (appsRes.ok) {
          const aData = await appsRes.json();
          setApplications(aData);
        }
      }
    } catch (e) {
      console.error('Error fetching data:', e);
    }
  };

  const handleOpenPreview = async (jobId: number) => {
    if (!candidate) return;
    try {
      const res = await fetch('/api/v1/applications/prepare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidate.id,
          job_id: jobId
        })
      });
      if (res.ok) {
        const preview = await res.json();
        setActivePreview(preview);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprove = async () => {
    if (!activePreview?.application_id) return;
    try {
      const res = await fetch(`/api/v1/applications/${activePreview.application_id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_approved: true })
      });
      if (res.ok) {
        setActivePreview(prev => prev ? { ...prev, candidate_approved: true, can_submit: true } : null);
        fetchInitialData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmit = async () => {
    if (!activePreview?.application_id) return;
    try {
      const res = await fetch(`/api/v1/applications/${activePreview.application_id}/submit`, {
        method: 'POST'
      });
      if (res.ok) {
        const result = await res.json();
        alert(`Application Confirmed! Ref: ${result.submission_ref_id}`);
        setActivePreview(null);
        fetchInitialData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const filteredJobs = jobs.filter(j => {
    const matchesSearch = !searchTerm || j.title.toLowerCase().includes(searchTerm.toLowerCase()) || j.company_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = !selectedCategory || j.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow font-bold text-xl">
                🧬
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-lg text-slate-900">Pharma Job Hunter AI</span>
                  <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-semibold">India</span>
                </div>
                <p className="text-xs text-slate-500">Autonomous Pharma Data Application Agent</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-semibold">
                Mode: <span className="text-emerald-700">Assisted with Approval</span>
              </div>
              <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-sm">
                {candidate?.user?.full_name ? candidate.user.full_name[0] : 'R'}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-100">
          <nav className="flex space-x-6">
            {(['dashboard', 'jobs', 'profile', 'applications', 'agents'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-1 border-b-2 font-medium text-sm capitalize transition-all ${
                  activeTab === tab
                    ? 'border-emerald-600 text-emerald-600 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Banner */}
            <div className="bg-gradient-to-r from-emerald-800 to-teal-700 rounded-2xl p-6 text-white shadow-md">
              <span className="px-2 py-0.5 bg-emerald-500/30 border border-emerald-400/40 rounded text-xs font-semibold uppercase">Live Multi-Agent System</span>
              <h1 className="text-2xl font-bold mt-2">Autonomous Life Sciences & Pharma Career Hub</h1>
              <p className="text-emerald-100 text-sm mt-1 max-w-2xl">
                Continuous discovery across 54 top Indian & Global pharma companies for engineering, analytics, AI, and clinical data roles.
              </p>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Jobs Discovered</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">{jobs.length}</h3>
                <p className="text-xs text-slate-400 mt-1">Across 54 Target Companies</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Active Vacancies</p>
                <h3 className="text-2xl font-bold text-emerald-600 mt-1">{jobs.filter(j => j.status === 'ACTIVE').length}</h3>
                <p className="text-xs text-emerald-600 mt-1">100% URL Verified</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Awaiting Approval</p>
                <h3 className="text-2xl font-bold text-amber-600 mt-1">{stats.awaiting_approval}</h3>
                <p className="text-xs text-amber-600 mt-1">Candidate Review Gate</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-500 uppercase">Submitted / Confirmed</p>
                <h3 className="text-2xl font-bold text-blue-600 mt-1">{stats.submitted + stats.confirmed}</h3>
                <p className="text-xs text-blue-600 mt-1">Receipt Ref Recorded</p>
              </div>
            </div>

            {/* Sector Coverage */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-800 mb-3">5 Indian Life Sciences Sectors Covered</h3>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded border">
                  <strong>Indian Pharma:</strong> Dr. Reddy's, Aurobindo, Sun, Cipla, Lupin, Zydus
                </div>
                <div className="p-3 bg-slate-50 rounded border">
                  <strong>Global Pharma:</strong> Pfizer, Roche, Novartis, Sanofi, AstraZeneca, GSK
                </div>
                <div className="p-3 bg-slate-50 rounded border">
                  <strong>CRO / CDMO:</strong> IQVIA, Parexel, ICON, Syneos Health, Labcorp
                </div>
                <div className="p-3 bg-slate-50 rounded border">
                  <strong>Biotech:</strong> Biocon Biologics, Serum Institute, Bharat Biotech, Syngene
                </div>
                <div className="p-3 bg-slate-50 rounded border">
                  <strong>Pharma Tech:</strong> AmpleLogic, Veeva, Indegene, Accenture Life Sciences
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="space-y-6">
            {/* Search & Filter */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
              <input
                type="text"
                placeholder="Search job title, skills, or company..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
              <select
                value={selectedCategory}
                onChange={e => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                <option value="">All Categories</option>
                <option value="Data Engineering">Data Engineering</option>
                <option value="Data Analytics">Data Analytics</option>
                <option value="AI and Machine Learning">AI and Machine Learning</option>
                <option value="Database and SQL">Database and SQL</option>
                <option value="Clinical and Pharmaceutical Data">Clinical and Pharmaceutical Data</option>
                <option value="Pharma IT and Data Quality">Pharma IT and Data Quality</option>
              </select>
            </div>

            {/* Jobs List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredJobs.map(job => (
                <div key={job.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold text-emerald-700 uppercase">{job.company_name}</span>
                    <h4 className="font-bold text-slate-900 text-base mt-1">{job.title}</h4>
                    <div className="flex flex-wrap gap-1.5 my-2 text-xs">
                      <span className="px-2 py-0.5 bg-slate-100 rounded">{job.city || job.location}</span>
                      <span className="px-2 py-0.5 bg-slate-100 rounded">{job.work_mode}</span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{job.description}</p>
                  </div>
                  <div className="mt-4 pt-3 border-t flex justify-between items-center">
                    <a href={job.official_application_url} target="_blank" rel="noreferrer" className="text-xs text-slate-500 hover:text-slate-800">
                      View Source &rarr;
                    </a>
                    <button
                      onClick={() => handleOpenPreview(job.id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold shadow-sm"
                    >
                      Apply (Assisted)
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b">
                <h3 className="font-bold text-slate-800">Application Tracking Pipeline</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-6">Position & Company</th>
                      <th className="py-3 px-6">Status</th>
                      <th className="py-3 px-6">Consent</th>
                      <th className="py-3 px-6">Ref ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y text-xs">
                    {applications.map(app => (
                      <tr key={app.id}>
                        <td className="py-4 px-6 font-semibold">{app.job_title} ({app.company_name})</td>
                        <td className="py-4 px-6">
                          <span className="px-2 py-1 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                            {app.status}
                          </span>
                        </td>
                        <td className="py-4 px-6">{app.candidate_approved ? '✅ Approved' : '⏳ Pending'}</td>
                        <td className="py-4 px-6 font-mono">{app.submission_ref_id || 'Pending'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Application Approval Modal */}
      {activePreview && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">Assisted Application Review</span>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{activePreview.job_title}</h3>
                <p className="text-xs text-emerald-700">{activePreview.company_name}</p>
              </div>
              <button onClick={() => setActivePreview(null)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto text-xs">
              <h4 className="font-bold text-slate-800">Truthful Screening Answers</h4>
              {activePreview.screening_questions.map((sq, idx) => (
                <div key={idx} className="p-3 bg-slate-50 rounded border">
                  <p className="font-semibold text-slate-800">{sq.question}</p>
                  <p className="text-emerald-700 mt-1 bg-emerald-50 p-2 rounded">{sq.answer}</p>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t flex justify-end space-x-2">
              <button onClick={() => setActivePreview(null)} className="px-4 py-2 border rounded text-xs font-semibold">Cancel</button>
              {!activePreview.candidate_approved ? (
                <button onClick={handleApprove} className="px-4 py-2 bg-emerald-600 text-white rounded text-xs font-semibold shadow">
                  Approve Application
                </button>
              ) : (
                <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded text-xs font-semibold shadow">
                  Submit Now
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

