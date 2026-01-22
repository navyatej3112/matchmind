import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Team {
  id: number
  name: string
}

interface FormResult {
  date: string
  opponent: string
  opponent_id: number
  home: boolean
  team_goals: number
  opponent_goals: number
  result: string
}

interface Form {
  team_id: number
  team_name: string
  last_n_results: FormResult[]
  points: number
  goal_difference: number
}

interface Prediction {
  home_team_id: number
  away_team_id: number
  season: string
  proba_home: number
  proba_draw: number
  proba_away: number
  explanation: {
    feature_contributions: Record<string, { value: number; contribution: number }>
    top_features: [string, { value: number; contribution: number }][]
  }
}

function App() {
  const [teams, setTeams] = useState<Team[]>([])
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null)
  const [form, setForm] = useState<Form | null>(null)
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [predictHomeTeam, setPredictHomeTeam] = useState<number | null>(null)
  const [predictAwayTeam, setPredictAwayTeam] = useState<number | null>(null)
  const [predictSeason, setPredictSeason] = useState('2023-24')

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    try {
      const response = await axios.get(`${API_URL}/teams`)
      setTeams(response.data)
    } catch (err) {
      setError('Failed to load teams')
      console.error(err)
    }
  }

  const fetchForm = async (teamId: number) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_URL}/analytics/form`, {
        params: { team_id: teamId, n: 5 }
      })
      setForm(response.data)
    } catch (err) {
      setError('Failed to load team form')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleTeamSelect = (teamId: number) => {
    setSelectedTeam(teamId)
    fetchForm(teamId)
  }

  const handlePredict = async () => {
    if (!predictHomeTeam || !predictAwayTeam) {
      setError('Please select both teams')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_URL}/predict`, {
        home_team_id: predictHomeTeam,
        away_team_id: predictAwayTeam,
        season: predictSeason
      })
      setPrediction(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to make prediction')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getResultColor = (result: string) => {
    switch (result) {
      case 'W': return '#10b981'
      case 'D': return '#f59e0b'
      case 'L': return '#ef4444'
      default: return '#6b7280'
    }
  }

  return (
    <div className="app">
      <header>
        <h1>⚽ MatchMind</h1>
        <p>Sports Analytics & Prediction</p>
      </header>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="container">
        <section className="card">
          <h2>Teams</h2>
          <div className="teams-grid">
            {teams.map(team => (
              <button
                key={team.id}
                className={`team-button ${selectedTeam === team.id ? 'active' : ''}`}
                onClick={() => handleTeamSelect(team.id)}
              >
                {team.name}
              </button>
            ))}
          </div>
        </section>

        {form && (
          <section className="card">
            <h2>Team Form: {form.team_name}</h2>
            <div className="form-stats">
              <div className="stat">
                <span className="stat-label">Points (Last 5)</span>
                <span className="stat-value">{form.points}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Goal Difference</span>
                <span className="stat-value">{form.goal_difference > 0 ? '+' : ''}{form.goal_difference}</span>
              </div>
            </div>
            <div className="results">
              {form.last_n_results.map((result, idx) => (
                <div key={idx} className="result-item">
                  <span className="result-date">{new Date(result.date).toLocaleDateString()}</span>
                  <span className="result-match">
                    {result.home ? 'H' : 'A'} vs {result.opponent}
                  </span>
                  <span className="result-score">
                    {result.team_goals} - {result.opponent_goals}
                  </span>
                  <span
                    className="result-badge"
                    style={{ backgroundColor: getResultColor(result.result) }}
                  >
                    {result.result}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="card">
          <h2>Match Prediction</h2>
          <div className="prediction-form">
            <div className="form-group">
              <label>Home Team</label>
              <select
                value={predictHomeTeam || ''}
                onChange={(e) => setPredictHomeTeam(Number(e.target.value) || null)}
              >
                <option value="">Select home team</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Away Team</label>
              <select
                value={predictAwayTeam || ''}
                onChange={(e) => setPredictAwayTeam(Number(e.target.value) || null)}
              >
                <option value="">Select away team</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Season</label>
              <select
                value={predictSeason}
                onChange={(e) => setPredictSeason(e.target.value)}
              >
                <option value="2021-22">2021-22</option>
                <option value="2022-23">2022-23</option>
                <option value="2023-24">2023-24</option>
              </select>
            </div>
            <button
              onClick={handlePredict}
              disabled={loading || !predictHomeTeam || !predictAwayTeam}
              className="predict-button"
            >
              {loading ? 'Predicting...' : 'Predict Match'}
            </button>
          </div>

          {prediction && (
            <div className="prediction-result">
              <h3>Prediction Results</h3>
              <div className="probabilities">
                <div className="prob-item">
                  <span className="prob-label">Home Win</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill"
                      style={{ width: `${prediction.proba_home * 100}%`, backgroundColor: '#10b981' }}
                    />
                    <span className="prob-value">{(prediction.proba_home * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="prob-item">
                  <span className="prob-label">Draw</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill"
                      style={{ width: `${prediction.proba_draw * 100}%`, backgroundColor: '#f59e0b' }}
                    />
                    <span className="prob-value">{(prediction.proba_draw * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="prob-item">
                  <span className="prob-label">Away Win</span>
                  <div className="prob-bar">
                    <div
                      className="prob-fill"
                      style={{ width: `${prediction.proba_away * 100}%`, backgroundColor: '#ef4444' }}
                    />
                    <span className="prob-value">{(prediction.proba_away * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="explanation">
                <h4>Top Contributing Features</h4>
                {prediction.explanation.top_features.map(([feature, data], idx) => (
                  <div key={idx} className="feature-item">
                    <span className="feature-name">{feature.replace(/_/g, ' ')}</span>
                    <span className="feature-value">Value: {data.value.toFixed(2)}</span>
                    <span className="feature-contrib">Contribution: {data.contribution.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default App

