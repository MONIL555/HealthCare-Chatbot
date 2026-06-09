import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  LayoutDashboard, MessageSquare, TrendingUp, Clock,
  ArrowLeft, Stethoscope, Heart, Activity, Zap
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalQueries: 0,
    recentQueries: [],
    topIntents: {},
    avgConfidence: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/chat/history?limit=50')
      .then((res) => {
        const queries = res.data.queries || [];
        const total = res.data.total_queries || 0;

        // Calculate stats
        const intentCounts = {};
        let totalConf = 0;
        queries.forEach((q) => {
          const intent = q.intent || 'general_query';
          intentCounts[intent] = (intentCounts[intent] || 0) + 1;
          totalConf += q.confidence || 0;
        });

        setStats({
          totalQueries: total,
          recentQueries: queries.slice(0, 5),
          topIntents: intentCounts,
          avgConfidence: queries.length > 0 ? totalConf / queries.length : 0,
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const topIntent = Object.entries(stats.topIntents).sort((a, b) => b[1] - a[1])[0];

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-5 flex items-center gap-4">
          <Link to="/chat" className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <LayoutDashboard className="w-5 h-5 text-blue-600" />
              Dashboard
            </h1>
            <p className="text-sm text-gray-500">Welcome, {user?.full_name || 'User'}</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-blue-600" />
                  </div>
                  <p className="text-sm text-gray-500">Total Queries</p>
                </div>
                <p className="text-3xl font-bold text-gray-900">{stats.totalQueries}</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-emerald-600" />
                  </div>
                  <p className="text-sm text-gray-500">Avg Confidence</p>
                </div>
                <p className="text-3xl font-bold text-gray-900">
                  {Math.round(stats.avgConfidence * 100)}%
                </p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center">
                    <Stethoscope className="w-5 h-5 text-purple-600" />
                  </div>
                  <p className="text-sm text-gray-500">Top Category</p>
                </div>
                <p className="text-lg font-bold text-gray-900 truncate">
                  {topIntent ? topIntent[0].replace('_', ' ') : '—'}
                </p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-amber-600" />
                  </div>
                  <p className="text-sm text-gray-500">Categories Used</p>
                </div>
                <p className="text-3xl font-bold text-gray-900">
                  {Object.keys(stats.topIntents).length}
                </p>
              </div>
            </div>

            {/* Intent Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  Intent Distribution
                </h3>
                {Object.keys(stats.topIntents).length === 0 ? (
                  <p className="text-sm text-gray-400 italic">No data yet</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(stats.topIntents)
                      .sort((a, b) => b[1] - a[1])
                      .map(([intent, count]) => {
                        const pct = stats.totalQueries > 0
                          ? Math.round((count / stats.totalQueries) * 100) : 0;
                        return (
                          <div key={intent}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-600 capitalize">
                                {intent.replace('_', ' ')}
                              </span>
                              <span className="text-xs text-gray-400">{count} ({pct}%)</span>
                            </div>
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full transition-all duration-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>

              {/* Recent Activity */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-600" />
                  Recent Activity
                </h3>
                {stats.recentQueries.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">No recent activity</p>
                ) : (
                  <div className="space-y-3">
                    {stats.recentQueries.map((q, i) => (
                      <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                        <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-gray-800 truncate">{q.query_text}</p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {q.created_at ? new Date(q.created_at).toLocaleString() : ''}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <Link
                  to="/history"
                  className="block mt-4 text-center text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  View All History →
                </Link>
              </div>
            </div>

            {/* Quick Action */}
            <div className="mt-6 text-center">
              <Link
                to="/chat"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-700 shadow-lg shadow-blue-200 transition-all"
              >
                <Heart className="w-4 h-4" />
                Start New Chat
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
