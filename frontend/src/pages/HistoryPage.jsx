import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import {
  History, ArrowLeft, ChevronLeft, ChevronRight,
  MessageSquare, Clock, TrendingUp, AlertTriangle,
  ChevronDown
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

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
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/chat"><ArrowLeft className="w-5 h-5" /></Link>
          </Button>
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <History className="w-5 h-5 text-primary" />
              Query History
            </h1>
            <p className="text-sm text-muted-foreground">{total} total queries</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : queries.length === 0 ? (
          <div className="text-center py-20">
            <MessageSquare className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">No queries yet. Start chatting!</p>
            <Button asChild>
              <Link to="/chat">Go to Chat</Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {queries.map((q, i) => (
              <Card key={q._id || i} className="overflow-hidden transition-all hover:shadow-md">
                <button
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  className="w-full text-left px-6 py-4 flex items-center justify-between gap-4 bg-card hover:bg-muted/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">{q.query_text}</p>
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                      <Badge variant="secondary" className="capitalize">
                        {q.category || q.intent?.replace('_', ' ')}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {Math.round((q.confidence || 0) * 100)}%
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {q.created_at ? new Date(q.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </div>
                  <ChevronDown className={`w-5 h-5 text-muted-foreground transition-transform ${expanded === i ? 'rotate-180' : ''}`} />
                </button>

                {expanded === i && (
                  <>
                    <Separator />
                    <CardContent className="px-6 py-4 bg-muted/10 space-y-4">
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Bot Response</p>
                        <p className="text-sm text-foreground bg-background border rounded-lg p-3">{q.response_text}</p>
                      </div>
                      
                      {q.recommendations?.home_remedies && q.recommendations.home_remedies.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-1.5">Remedies</p>
                          <ul className="text-sm space-y-1 bg-primary/5 border border-primary/10 rounded-lg p-3">
                            {q.recommendations.home_remedies.slice(0, 3).map((r, j) => (
                              <li key={j} className="flex items-start gap-2">
                                <span className="mt-1.5 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                                <span>{r}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 mt-8">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium text-muted-foreground">
              Page {page + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
