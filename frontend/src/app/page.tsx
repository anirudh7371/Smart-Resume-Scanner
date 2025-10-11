import UploadAndMatch from "@/components/UploadAndMatch";

export default function Home() {
  return (
    <div className="font-sans bg-gray-50 min-h-screen flex flex-col">
      {/* ---------- HEADER ---------- */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-5">
          <h1 className="text-3xl font-bold text-gray-800">
            Smart Resume Scanner
          </h1>
          <p className="text-gray-600">
            AI-Powered Resume Screening and Matching
          </p>
        </div>
      </header>

      {/* ---------- MAIN CONTENT ---------- */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-10">
        <UploadAndMatch />
      </main>

      {/* ---------- FOOTER ---------- */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-4 text-center text-gray-500 text-sm">
          © {new Date().getFullYear()} Smart Resume Scanner · Built with ❤️ by Anirudh
        </div>
      </footer>
    </div>
  );
}
