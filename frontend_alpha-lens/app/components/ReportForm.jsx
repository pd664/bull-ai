'use client';

import { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Loader2, Download, AlertCircle, X, TrendingUp, BarChart2, FileBarChart } from 'lucide-react';

const API_URL = 'http://localhost:8000';

const STEPS = ['Uploading', 'Extracting', 'Mapping', 'Generating'];

function StepProgress({ currentStep }) {
  return (
    <div className="flex items-start my-5">
      {STEPS.map((label, i) => {
        const done   = i < currentStep;
        const active = i === currentStep;
        return (
          <div key={i} className="flex flex-col items-center flex-1 relative">
            {/* connector line */}
            {i < STEPS.length - 1 && (
              <div className={`absolute top-[13px] left-1/2 w-full h-px z-0 transition-all duration-500
                ${done ? 'bg-emerald-500/50' : 'bg-white/[0.08]'}`}
              />
            )}
            {/* dot */}
            <div className={`relative z-10 w-[26px] h-[26px] rounded-full flex items-center justify-center text-[10px] font-mono mb-1.5 transition-all duration-300
              ${done  ? 'bg-emerald-500 text-slate-900 font-bold text-xs'
              : active ? 'bg-blue-500/20 border border-blue-400 text-blue-400'
              :          'bg-white/[0.05] border border-white/10 text-slate-500'}`}
            >
              {done ? '✓' : active
                ? <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                : i + 1
              }
            </div>
            <span className={`text-[9px] font-mono tracking-wide text-center leading-tight
              ${done ? 'text-emerald-400' : active ? 'text-blue-400' : 'text-slate-600'}`}>
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function ReportForm() {
  const [companyName, setCompanyName] = useState('');
  const [file, setFile]               = useState(null);
  const [status, setStatus]           = useState('idle');
  const [pdfUrl, setPdfUrl]           = useState(null);
  const [pdfFilename, setPdfFilename] = useState('');
  const [error, setError]             = useState('');
  const [dragging, setDragging]       = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const inputRef = useRef(null);
  const timerRef = useRef(null);

  function handleFileChange(selected) {
    if (!selected) return;
    setFile(selected);
    setStatus('idle');
    setError('');
    setPdfUrl(null);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileChange(dropped);
  }

  function runSteps() {
    setCurrentStep(0);
    let step = 0;
    timerRef.current = setInterval(() => {
      step++;
      if (step < STEPS.length) setCurrentStep(step);
      else clearInterval(timerRef.current);
    }, 1800);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!companyName.trim() || !file) return;

    setStatus('loading');
    setError('');
    setPdfUrl(null);
    runSteps();

    const formData = new FormData();
    formData.append('company_name', companyName.trim());
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/generate-report`, { method: 'POST', body: formData });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `Server error ${res.status}`);
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/pdf')) {
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const disp = res.headers.get('content-disposition') || '';
        const filename = disp.match(/filename="?([^"]+)"?/)?.[1] ||
          `${companyName.replace(/\s+/g, '_')}_report.pdf`;
        clearInterval(timerRef.current);
        setCurrentStep(STEPS.length);
        setPdfUrl(url);
        setPdfFilename(filename);
        setStatus('success');
      } else {
        const data = await res.json();
        throw new Error(data.error || 'Unexpected response from server');
      }
    } catch (err) {
      clearInterval(timerRef.current);
      setError(err.message);
      setStatus('error');
    }
  }

  function handleDownload() {
    const a = document.createElement('a');
    a.href = pdfUrl;
    a.download = pdfFilename;
    a.click();
  }

  function reset() {
    clearInterval(timerRef.current);
    setCompanyName('');
    setFile(null);
    setStatus('idle');
    setError('');
    setPdfUrl(null);
    setCurrentStep(0);
  }

  const canSubmit = companyName.trim() && file && status !== 'loading';

  return (
    <>
      <div className="relative min-h-screen bg-[#060a12] text-slate-200 flex flex-col overflow-hidden">

        {/* Background grid */}
        <div className="fixed inset-0 pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.028) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.028) 1px,transparent 1px)',
            backgroundSize: '52px 52px',
          }}
        />

        {/* Glow blobs */}
        <div className="fixed -top-48 -left-48 w-[600px] h-[600px] rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle,rgba(30,80,200,0.18) 0%,transparent 70%)' }}
        />
        <div className="fixed -bottom-36 -right-24 w-[500px] h-[500px] rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle,rgba(0,180,140,0.13) 0%,transparent 70%)' }}
        />

        {/* Nav */}
        <nav className="relative z-10 flex items-center justify-between px-12 py-[18px] border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5 font-syne font-extrabold text-xl tracking-tight text-white">
            <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)] animate-pulse" />
            BullAI
          </div>
          <span className="font-dmono text-[10px] tracking-[0.1em] text-blue-300/60 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded">
            EQUITY RESEARCH ENGINE
          </span>
        </nav>

        {/* Main content */}
        <main className="relative z-10 flex-1 flex items-center justify-center px-6 py-16">
          <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            {/* Left — Hero */}
            <div className="anim-fade">
              <p className="font-dmono text-[11px] tracking-[0.14em] text-emerald-400 uppercase mb-5 flex items-center gap-2">
                <span className="w-6 h-px bg-emerald-400 inline-block" />
                AI-Powered Research
              </p>

              <h1 className="font-syne font-extrabold text-[clamp(36px,4vw,52px)] leading-[1.08] tracking-tight text-white mb-5">
                Instant equity<br />
                reports,{' '}
                <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                  built by AI.
                </span>
              </h1>

              <p className="text-[15px] leading-relaxed text-slate-400 font-light max-w-md mb-10">
                Upload any financial document — earnings results, investor presentations,
                annual reports — and receive a Geojit-style research PDF in seconds.
              </p>

              <div className="flex flex-col gap-3">
                {[
                  { icon: <FileBarChart size={15} />, text: 'Geojit-style PDF with all sections & tables' },
                  { icon: <TrendingUp size={15} />,   text: 'LLM extracts financials, highlights & outlook' },
                  { icon: <BarChart2 size={15} />,    text: 'Revenue, margin & PAT charts auto-generated' },
                ].map(({ icon, text }) => (
                  <div key={text} className="flex items-center gap-3 text-[13px] text-slate-400">
                    <div className="w-8 h-8 rounded-lg bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-blue-400 flex-shrink-0">
                      {icon}
                    </div>
                    {text}
                  </div>
                ))}
              </div>
            </div>

            {/* Right — Card */}
            <div className="anim-fade-d relative rounded-2xl border border-white/[0.09] bg-white/[0.04] backdrop-blur-xl p-9 overflow-hidden">
              {/* Top shimmer line */}
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-400/50 to-transparent" />

              <h2 className="font-syne font-bold text-[17px] text-white mb-1 tracking-tight">
                Generate Research Report
              </h2>
              <p className="font-dmono text-[11px] text-slate-500 mb-7 tracking-wide">
                PDF · CSV · TXT accepted
              </p>

              <form onSubmit={handleSubmit} className="space-y-5">

                {/* Company name */}
                <div>
                  <label className="block font-dmono text-[11px] tracking-[0.1em] uppercase text-slate-500 mb-2">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g. ICICI Bank, JSW Energy…"
                    disabled={status === 'loading'}
                    className="w-full bg-white/[0.05] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600
                      focus:outline-none focus:border-blue-500/50 focus:bg-blue-500/[0.04]
                      disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  />
                </div>

                {/* File upload */}
                <div>
                  <label className="block font-dmono text-[11px] tracking-[0.1em] uppercase text-slate-500 mb-2">
                    Financial Document
                  </label>

                  {file ? (
                    <div className="flex items-center gap-3 bg-emerald-500/[0.07] border border-emerald-500/20 rounded-xl px-4 py-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 flex-shrink-0">
                        <FileText size={15} />
                      </div>
                      <span className="font-mono text-[12px] text-slate-300 flex-1 truncate">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => setFile(null)}
                        disabled={status === 'loading'}
                        className="text-slate-600 hover:text-red-400 transition-colors disabled:opacity-40"
                      >
                        <X size={15} />
                      </button>
                    </div>
                  ) : (
                    <div
                      onClick={() => inputRef.current?.click()}
                      onDrop={handleDrop}
                      onDragOver={e => { e.preventDefault(); setDragging(true); }}
                      onDragLeave={() => setDragging(false)}
                      className={`border-2 border-dashed rounded-xl px-4 py-7 text-center cursor-pointer transition-all
                        ${dragging
                          ? 'border-blue-400 bg-blue-500/[0.07]'
                          : 'border-white/[0.1] hover:border-blue-500/40 hover:bg-blue-500/[0.03]'
                        }`}
                    >
                      <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 mx-auto mb-3">
                        <Upload size={18} />
                      </div>
                      <p className="text-sm text-slate-400">
                        Drop file or <span className="text-blue-400">browse</span>
                      </p>
                      <p className="font-mono text-[10px] text-slate-600 mt-1.5 tracking-widest">
                        PDF · CSV · TXT · XLSX
                      </p>
                    </div>
                  )}

                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.csv,.txt,.xlsx,.xls"
                    className="hidden"
                    onChange={e => handleFileChange(e.target.files?.[0])}
                  />
                </div>

                {/* Step tracker */}
                {status === 'loading' && (
                  <StepProgress currentStep={currentStep} />
                )}

                {/* Error */}
                {status === 'error' && (
                  <div className="flex items-start gap-2.5 bg-red-500/[0.08] border border-red-500/25 rounded-xl px-4 py-3">
                    <AlertCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-[13px] text-red-400">{error}</p>
                  </div>
                )}

                {/* Success */}
                {status === 'success' && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2.5 bg-emerald-500/[0.08] border border-emerald-500/25 rounded-xl px-4 py-3">
                      <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] flex-shrink-0" />
                      <p className="text-[13px] text-emerald-400">Report generated successfully</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-syne font-bold text-sm
                        bg-gradient-to-r from-emerald-500 to-teal-500 text-white
                        hover:-translate-y-px hover:shadow-[0_8px_32px_rgba(52,211,153,0.35)] transition-all"
                    >
                      <Download size={15} />
                      Download PDF
                    </button>
                    <button
                      type="button"
                      onClick={reset}
                      className="w-full text-[11px] font-mono text-slate-600 hover:text-slate-400 transition-colors py-1 tracking-wider"
                    >
                      ← Generate another report
                    </button>
                  </div>
                )}

                {/* Submit */}
                {status !== 'success' && (
                  <button
                    type="submit"
                    disabled={!canSubmit}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-syne font-bold text-sm
                      bg-gradient-to-r from-blue-600 to-sky-500 text-white
                      hover:-translate-y-px hover:shadow-[0_8px_32px_rgba(37,99,235,0.4)]
                      disabled:from-white/[0.07] disabled:to-white/[0.07] disabled:text-slate-600
                      disabled:cursor-not-allowed disabled:shadow-none disabled:translate-y-0
                      transition-all duration-200"
                  >
                    {status === 'loading' ? (
                      <><Loader2 size={15} className="animate-spin" /> Processing…</>
                    ) : (
                      'Generate Report →'
                    )}
                  </button>
                )}
              </form>
            </div>

          </div>
        </main>

        {/* Footer */}
        <footer className="relative z-10 border-t border-white/[0.05] px-12 py-4 flex items-center justify-between">
          <p className="font-mono text-[10px] text-white tracking-wider">
            © 2025 BULLAI · EQUITY RESEARCH AUTOMATION
          </p>
          <p className="font-mono text-[10px] text-white tracking-wider">
            FASTAPI · GEMINI · REPORTLAB
          </p>
        </footer>

      </div>
    </>
  );
}