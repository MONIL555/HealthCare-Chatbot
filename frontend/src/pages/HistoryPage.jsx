import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import {
  History, ArrowLeft, ChevronLeft, ChevronRight,
  MessageSquare, Clock, TrendingUp, AlertTriangle
} from 'lucide-react';

const INTENT_COLORS = {
  symptoms_diagnosis: 'bg-amber-100 text-amber-800',
  medications_drugs: 'bg-purple-100 text-purple-800',
  emergency_urgent: 'bg-red-100 text-red-800',
  chronic_diseases: 'bg-teal-100 text-teal-800',
  womens_health: 'bg-pink-100 text-pink-800',
  dermatology: 'bg-orange-100 text-orange-800',
  orthopedics: 'bg-sky-100 text-sky-800',
  preventive_care: 'bg-emerald-100 text-emerald-800',
  general_query: 'bg-gray-100 text-gray-700',
};

export default function HistoryPage() {
  const [queries, setQueries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const limit = 10;

  useEffect(() => {
    setLoading(true);
    api.get(`/api/chat/history?limit=${limit}&offset=${page * limit}`)
      .then((res) => {
        setQueries(res.data.queries || []);
        setTotal(res.data.total_queries || 0);
      })
      .catch(() => setQueries([]))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-5 flex items-center gap-4">
          <Link to="/chat" className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <History className="w-5 h-5 text-blue-600" />
              Query History
            </h1>
            <p className="text-sm text-gray-500">{total} total queries</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : queries.length === 0 ? (
          <div className="text-center py-20">
            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No queries yet. Start chatting!</p>
            <Link to="/chat" className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors">
              Go to Chat
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {queries.map((q, i) => (
              <div
                key={q._id || i}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-sm transition-shadow"
              >
                <button
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  className="w-full text-left px-5 py-4 flex items-center gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{q.query_text}</p>
                    <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${INTENT_COLORS[q.intent] || INTENT_COLORS.general_query}`}>
                        {q.category || q.intent}
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {Math.round((q.confidence || 0) * 100)}%
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {q.created_at ? new Date(q.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${expanded === i ? 'rotate-90' : ''}`} />
                </button>

                {expanded === i && (
                  <div className="px-5 pb-4 pt-0 border-t border-gray-100">
                    <div className="mt-3 bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-gray-500 mb-1">Bot Response:</p>
                      <p className="text-sm text-gray-700">{q.response_text}</p>
                    </div>
                    {q.recommendations?.home_remedies && (
                      <div className="mt-2 bg-blue-50 rounded-lg p-3">
                        <p className="text-xs font-semibold text-blue-700 mb-1">Remedies:</p>
                        <ul className="text-xs text-blue-600 space-y-0.5">
                          {q.recommendations.home_remedies.slice(0, 3).map((r, j) => (
                            <li key={j}>• {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 mt-6">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="text-sm text-gray-600">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
