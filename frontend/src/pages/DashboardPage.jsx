import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';
import {
  LayoutDashboard, MessageSquare, TrendingUp, Clock,
  ArrowLeft, Stethoscope, Heart, Activity, Zap, User,
  Save, Loader2, ShieldAlert
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function DashboardPage() {
  const { user, setUser } = useAuth();
  const [stats, setStats] = useState({
    totalQueries: 0,
    recentQueries: [],
    topIntents: {},
    avgConfidence: 0,
  });
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  // Profile Form State
  const [profile, setProfile] = useState({
    age: '',
    gender: '',
    weight: '',
    height: '',
    medical_conditions: '',
    allergies: ''
  });

  useEffect(() => {
    // Load Stats
    api.get('/api/chat/history?limit=50')
      .then((res) => {
        const queries = res.data.queries || [];
        const total = res.data.total_queries || 0;

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

    // Load Profile
    if (user) {
      setProfile({
        age: user.age || '',
        gender: user.gender || '',
        weight: user.weight || '',
        height: user.height || '',
        medical_conditions: user.medical_conditions ? user.medical_conditions.join(', ') : '',
        allergies: user.allergies ? user.allergies.join(', ') : ''
      });
    }
  }, [user]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      // Split comma separated strings into arrays
      const conditions = profile.medical_conditions.split(',').map(s => s.trim()).filter(Boolean);
      const allergies = profile.allergies.split(',').map(s => s.trim()).filter(Boolean);

      const payload = {
        age: profile.age ? parseInt(profile.age) : null,
        gender: profile.gender || null,
        weight: profile.weight ? parseFloat(profile.weight) : null,
        height: profile.height ? parseFloat(profile.height) : null,
        medical_conditions: conditions,
        allergies: allergies
      };

      const res = await api.patch('/api/auth/profile', payload);
      setUser(res.data.user);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      toast.success('Profile updated successfully');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const topIntent = Object.entries(stats.topIntents).sort((a, b) => b[1] - a[1])[0];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/chat"><ArrowLeft className="w-5 h-5" /></Link>
          </Button>
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <LayoutDashboard className="w-5 h-5 text-primary" />
              Dashboard
            </h1>
            <p className="text-sm text-muted-foreground">Welcome back, {user?.full_name || 'User'}</p>
          </div>
          {user?.role === 'admin' && (
            <Button variant="outline" className="ml-auto bg-primary/10 text-primary border-primary/20 hover:bg-primary/20" asChild>
              <Link to="/admin"><ShieldAlert className="w-4 h-4 mr-2" /> Admin Panel</Link>
            </Button>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-[400px]">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="profile">Medical Profile</TabsTrigger>
          </TabsList>

          {/* ── OVERVIEW TAB ────────────────────────────────────── */}
          <TabsContent value="overview" className="space-y-6">
            {loading ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.totalQueries}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{Math.round(stats.avgConfidence * 100)}%</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Top Category</CardTitle>
                      <Stethoscope className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-lg font-bold truncate">
                        {topIntent ? topIntent[0].replace('_', ' ') : '—'}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Categories Used</CardTitle>
                      <Zap className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{Object.keys(stats.topIntents).length}</div>
                    </CardContent>
                  </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Activity className="w-4 h-4 text-primary" />
                        Intent Distribution
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {Object.keys(stats.topIntents).length === 0 ? (
                        <p className="text-sm text-muted-foreground">No data yet</p>
                      ) : (
                        <div className="space-y-4">
                          {Object.entries(stats.topIntents)
                            .sort((a, b) => b[1] - a[1])
                            .map(([intent, count]) => {
                              const pct = stats.totalQueries > 0
                                ? Math.round((count / stats.totalQueries) * 100) : 0;
                              return (
                                <div key={intent}>
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-medium capitalize">{intent.replace('_', ' ')}</span>
                                    <span className="text-xs text-muted-foreground">{count} ({pct}%)</span>
                                  </div>
                                  <Progress value={pct} className="h-2" />
                                </div>
                              );
                            })}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Clock className="w-4 h-4 text-primary" />
                        Recent Activity
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {stats.recentQueries.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No recent activity</p>
                      ) : (
                        <div className="space-y-4">
                          {stats.recentQueries.map((q, i) => (
                            <div key={i} className="flex items-start gap-4 text-sm">
                              <div className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                              <div className="min-w-0 flex-1">
                                <p className="font-medium truncate">{q.query_text}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {q.created_at ? new Date(q.created_at).toLocaleString() : ''}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                    <CardFooter className="pt-0">
                      <Button variant="link" asChild className="px-0">
                        <Link to="/history">View All History →</Link>
                      </Button>
                    </CardFooter>
                  </Card>
                </div>
              </>
            )}
          </TabsContent>

          {/* ── PROFILE TAB ────────────────────────────────────── */}
          <TabsContent value="profile">
            <Card>
              <form onSubmit={handleProfileUpdate}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5 text-primary" />
                    Medical Profile
                  </CardTitle>
                  <CardDescription>
                    Provide your medical context so the AI can give more personalized recommendations.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="age">Age</Label>
                      <Input
                        id="age"
                        type="number"
                        placeholder="e.g. 35"
                        value={profile.age}
                        onChange={(e) => setProfile({...profile, age: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="gender">Biological Gender</Label>
                      <Select
                        value={profile.gender}
                        onValueChange={(val) => setProfile({...profile, gender: val})}
                      >
                        <SelectTrigger id="gender">
                          <SelectValue placeholder="Select gender" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="male">Male</SelectItem>
                          <SelectItem value="female">Female</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="weight">Weight (kg)</Label>
                      <Input
                        id="weight"
                        type="number"
                        step="0.1"
                        placeholder="e.g. 70.5"
                        value={profile.weight}
                        onChange={(e) => setProfile({...profile, weight: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="height">Height (cm)</Label>
                      <Input
                        id="height"
                        type="number"
                        placeholder="e.g. 175"
                        value={profile.height}
                        onChange={(e) => setProfile({...profile, height: e.target.value})}
                      />
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label htmlFor="conditions">Pre-existing Medical Conditions</Label>
                    <Textarea
                      id="conditions"
                      placeholder="e.g. Hypertension, Asthma, Type 2 Diabetes (comma separated)"
                      value={profile.medical_conditions}
                      onChange={(e) => setProfile({...profile, medical_conditions: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="allergies">Known Allergies</Label>
                    <Textarea
                      id="allergies"
                      placeholder="e.g. Penicillin, Peanuts, Pollen (comma separated)"
                      value={profile.allergies}
                      onChange={(e) => setProfile({...profile, allergies: e.target.value})}
                    />
                  </div>
                </CardContent>
                <CardFooter className="bg-muted/50 py-4 flex justify-end">
                  <Button type="submit" disabled={savingProfile}>
                    {savingProfile ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                    Save Profile
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
