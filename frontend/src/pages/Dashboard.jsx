import { useState, useEffect } from 'react';
import {
  Wallet,
  TrendingDown,
  FileSearch,
  AlertCircle,
  RefreshCcw,
} from 'lucide-react';
import { fetchDashboard, fetchForecast, fetchAffordabilityHistory } from '../api/client';
import BurnRateChart from '../components/BurnRateChart';
import CashFlowChart from '../components/CashFlowChart';
import ExpenseForm from '../components/ExpenseForm';
import DecisionCard from '../components/DecisionCard';
import AffordabilityHistory from '../components/AffordabilityHistory';

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [history, setHistory] = useState([]);
  const [latestResult, setLatestResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [dashRes, forecastRes, historyRes] = await Promise.all([
        fetchDashboard(),
        fetchForecast(30),
        fetchAffordabilityHistory({ limit: 10 }),
      ]);
      setDashboard(dashRes.data);
      setForecast(forecastRes.data.forecast || []);
      setHistory(historyRes.data.checks || []);
      
      if (dashRes.data.latest_check) {
        setLatestResult(dashRes.data.latest_check);
      }
    } catch (err) {
      setError('Failed to load dashboard data. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleResult = (result) => {
    setLatestResult(result);
    loadData();
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-24 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="skeleton h-80 rounded-xl" />
          <div className="skeleton h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-headline text-2xl font-bold">Dashboard</h2>
          <p className="text-sm" style={{ color: 'var(--color-on-surface-variant)' }}>
            Your financial health at a glance
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadData}>
          <RefreshCcw size={16} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="card-glass flex items-center gap-3 text-sm" style={{ color: 'var(--color-defer)' }}>
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-glass">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'var(--color-primary-container)' }}
            >
              <Wallet size={20} style={{ color: 'var(--color-primary)' }} />
            </div>
            <div>
              <p className="text-label">Current Balance</p>
              <p className="text-display text-xl">
                ₹{(dashboard?.current_balance || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card-glass">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(220, 38, 38, 0.08)' }}
            >
              <TrendingDown size={20} style={{ color: 'var(--color-critical)' }} />
            </div>
            <div>
              <p className="text-label">Monthly Burn Rate</p>
              <p className="text-display text-xl">
                ₹{(dashboard?.monthly_burn_rate || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card-glass">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(217, 119, 6, 0.08)' }}
            >
              <FileSearch size={20} style={{ color: 'var(--color-defer)' }} />
            </div>
            <div>
              <p className="text-label">Needs Review</p>
              <p className="text-display text-xl">
                {dashboard?.needs_review_count || 0}
                <span className="text-sm font-normal ml-1" style={{ color: 'var(--color-on-surface-variant)' }}>
                  of {dashboard?.total_transactions || 0}
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 grid-dashboard">
        {/* Burn Rate Donut */}
        <div className="card-glass">
          <h3 className="text-headline text-base font-semibold mb-4">
            Monthly Burn by Category
          </h3>
          <BurnRateChart data={dashboard?.category_breakdown || {}} />
        </div>

        {/* Cash Flow Forecast */}
        <div className="card-glass">
          <h3 className="text-headline text-base font-semibold mb-4">
            30-Day Cash Flow Forecast
          </h3>
          <CashFlowChart
            data={forecast}
            currentBalance={dashboard?.current_balance || 0}
          />
        </div>
      </div>

      {/* Expense Form + Decision Card */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 grid-dashboard">
        <div className="card-glass">
          <ExpenseForm onResult={handleResult} />
        </div>

        <div>
          {latestResult ? (
            <DecisionCard result={latestResult} />
          ) : (
            <div
              className="card-glass flex items-center justify-center h-full min-h-[200px] text-sm"
              style={{ color: 'var(--color-on-surface-variant)' }}
            >
              Submit an expense to see the affordability result
            </div>
          )}
        </div>
      </div>

      {/* History */}
      <div className="card-glass">
        <h3 className="text-headline text-base font-semibold mb-4">
          Recent Affordability Checks
        </h3>
        <AffordabilityHistory checks={history} />
      </div>
    </div>
  );
}
