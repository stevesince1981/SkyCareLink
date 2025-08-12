import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  const handleTestClick = () => {
    navigate('/phase-1');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex items-center justify-center">
      <div className="text-center">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">MediFly</h1>
          <p className="text-xl text-gray-600 mb-2">Medical Transport Dashboard</p>
          <p className="text-gray-500">Phase 1 Preview Application</p>
        </div>
        
        <div className="mb-8">
          <div className="w-24 h-24 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </div>
          <p className="text-gray-600">Ready to preview the dashboard interface</p>
        </div>

        <button
          onClick={handleTestClick}
          data-test="btn-test"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg text-lg transition-colors duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-transform">
          Test Dashboard
        </button>

        <div className="mt-8 text-sm text-gray-500">
          <p>Click the button above to access the Phase 1 dashboard with role-based views</p>
        </div>
      </div>
    </div>
  );
}