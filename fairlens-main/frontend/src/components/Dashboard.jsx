import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { FiArrowLeft, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';

const Dashboard = ({ results, onReset }) => {
  const { accuracy, bias_score, fairness_metrics, feature_importance, counterfactuals, recommendations } = results;

  // Format Feature Importance for Recharts
  const chartData = Object.keys(feature_importance).map(key => ({
    name: key,
    value: parseFloat((feature_importance[key] * 100).toFixed(2))
  })).sort((a, b) => b.value - a.value);

  // Score Color Helper
  const getScoreClass = (score) => {
    if (score > 40) return 'score-high';
    if (score > 15) return 'score-medium';
    return 'score-low';
  };

  const scoreClass = getScoreClass(bias_score);

  return (
    <div className="dashboard-grid">
      
      {/* Header Row */}
      <div className="col-span-12" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn" onClick={onReset} style={{ background: '#E2E8F0' }}>
          <FiArrowLeft /> Back to Upload
        </button>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '700' }}>Audit Results</h2>
      </div>

      {/* Main Score & Accuracy */}
      <div className="card col-span-6" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div className={`metric-value ${scoreClass}`}>
          {bias_score.toFixed(0)} <span style={{fontSize:'1.25rem', color:'var(--text-muted)'}}>/ 100</span>
        </div>
        <div className="metric-label">Overall Bias Score</div>
        
        {bias_score > 40 ? (
          <div style={{ marginTop: '1rem', color: 'var(--error-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <FiAlertTriangle /> High Bias Detected
          </div>
        ) : (
          <div style={{ marginTop: '1rem', color: 'var(--success-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <FiCheckCircle /> Acceptable Bias Levels
          </div>
        )}
      </div>

      <div className="card col-span-6" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div className="metric-value">{(accuracy * 100).toFixed(1)}%</div>
        <div className="metric-label">Model Accuracy</div>
        <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Accuracy of the underlying predictive model.
        </p>
      </div>

      {/* Recommendations */}
      <div className="card col-span-12">
        <div className="card-title">Recommendations</div>
        {recommendations.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No critical recommendations at this time.</p>
        ) : (
          <ul className="rec-list">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="rec-item">
                <FiAlertTriangle style={{ color: 'var(--warning-color)', marginTop: '0.2rem' }} />
                <p>{rec}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Feature Importance Chart */}
      <div className="card col-span-6">
        <div className="card-title">Feature Importance (SHAP)</div>
        <div style={{ height: '300px', width: '100%', marginTop: '1.5rem' }}>
          <ResponsiveContainer>
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} />
              <Tooltip cursor={{fill: 'rgba(59, 130, 246, 0.05)'}} formatter={(value) => `${value}%`} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {
                  chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={'var(--primary-color)'} opacity={0.8 + (index * 0.05)} />
                  ))
                }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Counterfactual Cases */}
      <div className="card col-span-6">
         <div className="card-title">Counterfactual Evidence</div>
         <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
           Instances where changing a sensitive attribute reversed the model's decision.
         </p>
         
         <div style={{ overflowX: 'auto', maxHeight: '300px' }}>
           {counterfactuals.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
                 No counterfactual flips discovered!
              </div>
           ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Flip Condition</th>
                  <th>Result Changed To</th>
                </tr>
              </thead>
              <tbody>
                {counterfactuals.map((cf, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{cf.name}</td>
                    <td>
                      <span style={{color: 'var(--text-muted)'}}>{cf.original_value}</span>
                      <span style={{margin: '0 0.25rem'}}>→</span> 
                      {cf.flipped_value}
                    </td>
                    <td>
                      <span className={`badge ${cf.new_decision.toLowerCase() === 'selected' ? 'badge-selected' : 'badge-rejected'}`}>
                        {cf.new_decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
           )}
         </div>
      </div>

    </div>
  );
};

export default Dashboard;
