"use client";

import { useState } from "react";
import axios from "axios";

interface MatchResult {
  candidate_name: string;
  match_score: number;
  justification: string;
  strengths: string[];
  gaps: string[];
}

interface ParseResponse {
  raw_text: string;
}

const UploadAndMatch = () => {
  const [file, setFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !jobTitle || !jobDescription) {
      setError("Please fill in all fields and select a resume file.");
      return;
    }

    setIsLoading(true);
    setError("");
    setMatchResult(null);

    try {
      // Step 1: Parse resume
      const formData = new FormData();
      formData.append("file", file);

      const parseResponse = await axios.post<ParseResponse>(
        "http://localhost:8000/api/v1/parse",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      const resumeText = parseResponse.data.raw_text;

      // Step 2: Match against job description
      const matchFormData = new FormData();
      matchFormData.append("resume_text", resumeText);
      matchFormData.append("job_title", jobTitle);
      matchFormData.append("job_description", jobDescription);
      matchFormData.append("required_skills", requiredSkills);

      const matchResponse = await axios.post<MatchResult>(
        "http://localhost:8000/api/v1/match",
        matchFormData
      );

      setMatchResult(matchResponse.data);
    } catch (err) {
      console.error("Error during analysis:", err);
      setError("An error occurred while analyzing. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* ---------- LEFT SIDE: INPUT FORM ---------- */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-semibold mb-4">Job & Resume Details</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="jobTitle" className="block text-gray-700 font-medium mb-2">
              Job Title
            </label>
            <input
              type="text"
              id="jobTitle"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="jobDescription" className="block text-gray-700 font-medium mb-2">
              Job Description
            </label>
            <textarea
              id="jobDescription"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={6}
              className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="requiredSkills" className="block text-gray-700 font-medium mb-2">
              Required Skills (comma-separated)
            </label>
            <input
              type="text"
              id="requiredSkills"
              value={requiredSkills}
              onChange={(e) => setRequiredSkills(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="resume" className="block text-gray-700 font-medium mb-2">
              Upload Resume
            </label>
            <input
              type="file"
              id="resume"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileChange}
              className="w-full text-sm text-gray-500 
                         file:mr-4 file:py-2 file:px-4 
                         file:rounded-full file:border-0 
                         file:text-sm file:font-semibold 
                         file:bg-indigo-50 file:text-indigo-700 
                         hover:file:bg-indigo-100"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md 
                       hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors"
          >
            {isLoading ? "Analyzing..." : "Find Best Match"}
          </button>
        </form>

        {error && <p className="text-red-500 mt-4">{error}</p>}
      </div>

      {/* ---------- RIGHT SIDE: RESULTS ---------- */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-semibold mb-4">Match Result</h2>
        {isLoading && <p>Analyzing resume and job description...</p>}

        {matchResult && (
          <div>
            <h3 className="text-xl font-semibold mb-2">
              Candidate: {matchResult.candidate_name}
            </h3>
            <p className="text-lg font-medium text-indigo-600">
              Match Score: {matchResult.match_score}/10
            </p>
            <p className="mt-2 text-gray-700">{matchResult.justification}</p>

            <div className="mt-4">
              <h4 className="font-semibold">Strengths:</h4>
              <ul className="list-disc list-inside text-gray-600">
                {matchResult.strengths?.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>

            <div className="mt-4">
              <h4 className="font-semibold">Gaps:</h4>
              <ul className="list-disc list-inside text-gray-600">
                {matchResult.gaps?.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadAndMatch;
