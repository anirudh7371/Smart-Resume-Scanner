"use client";
import { Award, Zap, Shield, TrendingUp, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* HEADER */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10 border-b border-indigo-100">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Award className="w-8 h-8 text-indigo-600" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Smart Resume Matcher
            </h1>
          </div>
          <button
            onClick={() => router.push('/matcher')}
            className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all"
          >
            Get Started
          </button>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 rounded-full text-indigo-700 text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            AI-Powered Recruitment
          </div>
          <h2 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Find the Perfect Candidate
            <br />
            <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              In Seconds
            </span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Leverage advanced AI to automatically screen, rank, and analyze resumes against your job descriptions.
            Save time, reduce bias, and hire smarter.
          </p>
          <button
            onClick={() => router.push('/matcher')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-indigo-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
          >
            Start Matching Now
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* DEMO IMAGE PLACEHOLDER */}
        <div className="mt-16 bg-white rounded-2xl shadow-2xl p-8 border border-indigo-100">
          <div className="aspect-video bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center">
            <div className="text-center">
              <Award className="w-24 h-24 text-indigo-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">Dashboard Preview</p>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <h3 className="text-4xl font-bold text-center text-gray-900 mb-16">
          Why Choose Smart Resume Matcher?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-indigo-100 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-3">Lightning Fast</h4>
            <p className="text-gray-600">
              Analyze hundreds of resumes in seconds. Our AI processes and ranks candidates instantly, saving you hours of manual screening.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-indigo-100 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-3">Smart Matching</h4>
            <p className="text-gray-600">
              Advanced AI algorithms understand context and semantics, matching candidates based on skills, experience, and relevance.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-indigo-100 hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-3">Fair & Unbiased</h4>
            <p className="text-gray-600">
              Focus on skills and qualifications. Our system evaluates candidates objectively, helping you build diverse teams.
            </p>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h3 className="text-4xl font-bold text-center text-gray-900 mb-16">
            How It Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Step 1 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                1
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Upload Job Description</h4>
              <p className="text-gray-600">
                Paste your job description or upload a file. Our AI will understand the requirements.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                2
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Upload Resumes</h4>
              <p className="text-gray-600">
                Bulk upload candidate resumes in PDF or DOCX format. No limit on the number.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                3
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Get Ranked Results</h4>
              <p className="text-gray-600">
                Review top candidates with match scores, strengths, gaps, and download detailed PDF reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl p-12 text-center text-white shadow-2xl">
          <h3 className="text-4xl font-bold mb-4">Ready to Transform Your Hiring?</h3>
          <p className="text-xl mb-8 opacity-90">
            Join hundreds of recruiters who are hiring smarter with AI
          </p>
          <button
            onClick={() => router.push('/matcher')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-indigo-600 rounded-xl font-semibold text-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg"
          >
            Start For Free
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-white border-t mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-gray-600 text-sm">
          © {new Date().getFullYear()} Smart Resume Matcher · Built with ❤️ by Anirudh
        </div>
      </footer>
    </div>
  );
}