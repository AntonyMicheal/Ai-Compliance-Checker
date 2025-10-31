//App.jsx
import { useState } from 'react';
import axios from 'axios';
import './index.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResults(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/check`, {
        url: url
      });
      setResults(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        'Failed to check compliance. Please ensure the URL is valid and accessible.'
      );
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pass':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'fail':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pass':
        return '✓';
      case 'fail':
        return '✗';
      default:
        return '!';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            🔍 AI Compliance Checker
          </h1>
          <p className="text-xl text-gray-600">
            Analyze web accessibility and get AI-powered recommendations
          </p>
        </header>

        {/* Input Form */}
        <div className="max-w-3xl mx-auto mb-8">
          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter website URL (e.g., https://example.com)"
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-indigo-500 text-lg"
                required
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Checking...' : 'Run Check'}
              </button>
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-3xl mx-auto mb-8">
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
              <p className="text-red-800 font-medium">❌ {error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="max-w-3xl mx-auto text-center">
            <div className="bg-white rounded-lg shadow-lg p-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-gray-600 text-lg">Analyzing webpage...</p>
            </div>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="max-w-5xl mx-auto">
            {/* Score Card */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">
                    Compliance Report
                  </h2>
                  <p className="text-gray-600">{results.url}</p>
                </div>
                <div className="text-center">
                  <div className="text-6xl font-bold text-indigo-600 mb-2">
                    {results.score}/10
                  </div>
                  <p className="text-gray-600 font-medium">Overall Score</p>
                </div>
              </div>
              
              <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-600 mb-1">Total Checks</p>
                  <p className="text-3xl font-bold text-gray-800">{results.total_checks}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-green-700 mb-1">Passed</p>
                  <p className="text-3xl font-bold text-green-600">{results.passed_checks}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-red-700 mb-1">Failed</p>
                  <p className="text-3xl font-bold text-red-600">{results.failed_checks}</p>
                </div>
              </div>
            </div>

            {/* Detailed Results */}
            <div className="space-y-4">
              {results.results.map((result, index) => (
                <div
                  key={index}
                  className={`bg-white rounded-lg shadow-md overflow-hidden border-l-4 ${
                    result.status === 'pass' 
                      ? 'border-green-500' 
                      : result.status === 'fail'
                      ? 'border-red-500'
                      : 'border-yellow-500'
                  }`}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-2xl font-bold px-3 py-1 rounded ${getStatusColor(
                            result.status
                          )}`}
                        >
                          {getStatusIcon(result.status)}
                        </span>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800">
                            {result.check}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {result.details}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`px-4 py-1 rounded-full text-sm font-semibold ${getStatusColor(
                          result.status
                        )}`}
                      >
                        {result.status.toUpperCase()}
                      </span>
                    </div>

                    {/* AI Recommendation */}
                    {result.recommendation && (
                      <div className="mt-4 bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                        <div className="flex items-start gap-2">
                          <span className="text-blue-600 text-xl">💡</span>
                          <div>
                            <p className="font-semibold text-blue-900 mb-2">
                              AI Recommendation:
                            </p>
                            <p className="text-gray-700 leading-relaxed">
                              {result.recommendation}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 text-center text-gray-600">
          <p className="mb-2">
            Built with FastAPI, React, and Claude AI
          </p>
          <p className="text-sm">
            Checks based on WCAG 2.1 accessibility guidelines
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;