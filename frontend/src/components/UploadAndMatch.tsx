"use client";
import { useState, ChangeEvent } from 'react';
import { Upload, FileText, Briefcase, Award, TrendingUp, X, Download } from 'lucide-react';

interface Candidate {
  candidate_name: string;
  filename: string;
  match_score: number;
  justification: string;
  strengths: string[];
  gaps: string[];
}

interface MatchResults {
  top_candidates: Candidate[];
  resume_texts: Record<string, string>;
}

export default function ResumeMatcherUI() {
  const [jobDescFile, setJobDescFile] = useState<File | null>(null);
  const [jobDescText, setJobDescText] = useState<string>('');
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [topK, setTopK] = useState<number>(5);
  const [results, setResults] = useState<MatchResults | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleJobDescFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setJobDescFile(file);
      setJobDescText('');
    }
  };

  const handleResumeFilesChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setResumeFiles(files);
  };

  const removeResume = (index: number) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if ((!jobDescFile && !jobDescText.trim()) || resumeFiles.length === 0) {
      setError('Please provide a job description and at least one resume');
      return;
    }

    setIsLoading(true);
    setError('');
    setResults(null);

    try {
      const formData = new FormData();

      if (jobDescFile) {
        formData.append('job_description_file', jobDescFile);
      } else {
        formData.append('job_description_text', jobDescText);
      }

      resumeFiles.forEach((file) => {
        formData.append('resume_files', file);
      });

      formData.append('top_k', topK.toString());

      const response = await fetch('http://localhost:8000/api/v1/match-multiple', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to analyze resumes');

      const data: MatchResults = await response.json();
      setResults(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred during analysis');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const downloadPDFReport = async () => {
    if (!results) return;

    setIsGeneratingPDF(true);
    try {
      const formData = new FormData();
      formData.append('job_description_text', jobDescText || 'Job Description from uploaded file');
      formData.append('candidates_json', JSON.stringify(results.top_candidates));
      formData.append('resume_texts_json', JSON.stringify(results.resume_texts || {}));

      const response = await fetch('http://localhost:8000/api/v1/generate-report', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to generate PDF report');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'candidate_analysis_report.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to generate PDF report');
      }
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* HEADER */}
      <div className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10 border-b border-indigo-100">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <Award className="w-8 h-8 text-indigo-600" />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Smart Resume Matcher
              </h1>
              <p className="text-gray-600 text-sm">AI-Powered Candidate Screening</p>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* LEFT PANEL */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-indigo-100">
              <div className="flex items-center gap-2 mb-6">
                <Briefcase className="w-6 h-6 text-indigo-600" />
                <h2 className="text-2xl font-semibold text-gray-800">Job Description</h2>
              </div>

              {/* Upload Job Description */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Upload Job Description (PDF/DOCX) or Paste Below
                  </label>

                  <div className="relative">
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={handleJobDescFileChange}
                      className="hidden"
                      id="job-file-input"
                    />
                    <label
                      htmlFor="job-file-input"
                      className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-indigo-300 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors bg-indigo-50/50"
                    >
                      <Upload className="w-5 h-5 text-indigo-600" />
                      <span className="text-sm text-gray-700">
                        {jobDescFile ? jobDescFile.name : 'Choose file'}
                      </span>
                    </label>
                  </div>

                  <div className="relative my-4">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-white text-gray-500">OR</span>
                    </div>
                  </div>

                  <textarea
                    value={jobDescText}
                    onChange={(e) => {
                      setJobDescText(e.target.value);
                      if (e.target.value) setJobDescFile(null);
                    }}
                    placeholder="Paste job description here..."
                    rows={8}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-gray-900 placeholder-gray-400"
                  />
                </div>

                {/* Upload Resumes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Upload Candidate Resumes (PDF/DOCX)
                  </label>

                  <div className="relative">
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      multiple
                      onChange={handleResumeFilesChange}
                      className="hidden"
                      id="resume-files-input"
                    />
                    <label
                      htmlFor="resume-files-input"
                      className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-purple-300 rounded-lg cursor-pointer hover:border-purple-500 transition-colors bg-purple-50/50"
                    >
                      <FileText className="w-5 h-5 text-purple-600" />
                      <span className="text-sm text-gray-700">
                        {resumeFiles.length > 0
                          ? `${resumeFiles.length} resume(s) selected`
                          : 'Choose resume files'}
                      </span>
                    </label>
                  </div>

                  {resumeFiles.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {resumeFiles.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg"
                        >
                          <span className="text-sm text-gray-700 truncate">{file.name}</span>
                          <button
                            type="button"
                            onClick={() => removeResume(index)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Top K */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Top K Candidates
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
                  />
                </div>

                {/* Submit */}
                <button
                  onClick={handleSubmit}
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Analyzing...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      Find Best Matches
                    </span>
                  )}
                </button>

                {error && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT PANEL */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-indigo-100">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">Top Candidates</h2>
              {results && (
                <button
                  onClick={downloadPDFReport}
                  disabled={isGeneratingPDF}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                >
                  {isGeneratingPDF ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Download Report
                    </>
                  )}
                </button>
              )}
            </div>

            {!results && !isLoading && (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <Award className="w-16 h-16 mb-4 opacity-50" />
                <p className="text-center">Results will appear here after analysis</p>
              </div>
            )}

            {isLoading && (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600">Analyzing candidates...</p>
              </div>
            )}

            {results && (
              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                {results.top_candidates.map((candidate: Candidate, index: number) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow bg-gradient-to-br from-white to-gray-50"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                          #{index + 1}
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg text-gray-800">
                            {candidate.candidate_name}
                          </h3>
                          <p className="text-sm text-gray-500">{candidate.filename}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-indigo-600">
                          {candidate.match_score}
                        </div>
                        <div className="text-xs text-gray-500">/ 10</div>
                      </div>
                    </div>

                    <p className="text-sm text-gray-700 mb-4 leading-relaxed">
                      {candidate.justification}
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-sm text-green-700 mb-2">Strengths</h4>
                        <ul className="space-y-1">
                          {candidate.strengths.slice(0, 3).map((strength: string, i: number) => (
                            <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
                              <span className="text-green-500 mt-0.5">✓</span>
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-medium text-sm text-orange-700 mb-2">Gaps</h4>
                        <ul className="space-y-1">
                          {candidate.gaps.slice(0, 3).map((gap: string, i: number) => (
                            <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
                              <span className="text-orange-500 mt-0.5">⚠</span>
                              <span>{gap}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}