
import { useState } from 'react'
import {
  Activity,
  Bot,
  Headset,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Send,
  Sparkles,
  User,
  Wrench,
} from 'lucide-react'

const API_URL = 'http://localhost:8000'

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem('access_token') || ''
  )
  const [username, setUsername] = useState(
    () => localStorage.getItem('username') || ''
  )

  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const [loginError, setLoginError] = useState('')

  const [activeView, setActiveView] = useState('chat')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content:
        'Olá! Sou o assistente inteligente da Getnet. Como posso ajudar você hoje?',
    },
  ])

  async function handleLogin(event) {
    event.preventDefault()

    if (!loginUsername.trim() || !loginPassword) {
      setLoginError('Informe seu usuário e sua senha.')
      return
    }

    setLoginLoading(true)
    setLoginError('')

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginUsername.trim(),
          password: loginPassword,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Usuário ou senha incorretos.')
      }

      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('username', loginUsername.trim())

      setToken(data.access_token)
      setUsername(loginUsername.trim())
      setLoginPassword('')
      setLoginError('')
    } catch (err) {
      setLoginError(
        `${err.message} Verifique se a API está rodando.`
      )
    } finally {
      setLoginLoading(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')

    setToken('')
    setUsername('')
    setLoginUsername('')
    setLoginPassword('')
    setInput('')
    setError('')
    setActiveView('chat')

    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content:
          'Olá! Sou o assistente inteligente da Getnet. Como posso ajudar você hoje?',
      },
    ])
  }

  const userMessages = messages.filter(
    (message) => message.role === 'user'
  )

  const assistantMessages = messages.filter(
    (message) =>
      message.role === 'assistant' && message.target_agent
  )

  const agentsUsed = new Set(
    assistantMessages.map((message) => message.target_agent)
  ).size

  const toolsUsed = assistantMessages.reduce(
    (total, message) => total + (message.tools_used?.length || 0),
    0
  )

  const tokenUsage = assistantMessages.reduce(
    (total, message) => ({
      input_tokens: total.input_tokens + (message.token_usage?.input_tokens || 0),
      output_tokens: total.output_tokens + (message.token_usage?.output_tokens || 0),
      total_tokens: total.total_tokens + (message.token_usage?.total_tokens || 0),
    }),
    { input_tokens: 0, output_tokens: 0, total_tokens: 0 }
  )

  async function sendMessage(text = input) {
    const question = text.trim()

    if (!question || loading || !token) return

    setError('')
    setInput('')

    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        role: 'user',
        content: question,
      },
    ])

    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: question,
        }),
      })

      const data = await response.json()

      if (response.status === 401) {
        handleLogout()
        setLoginError('Sua sessão expirou. Faça login novamente.')
        return
      }

      if (!response.ok) {
        throw new Error(
          data.detail || 'Não foi possível consultar o assistente.'
        )
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.response,
          status: data.status,
          target_agent: data.target_agent,
          intent: data.intent,
          tools_used: data.tools_used || [],
          sources: data.sources || [],
          token_usage: data.token_usage || {
            input_tokens: 0,
            output_tokens: 0,
            total_tokens: 0,
          },
        },
      ])
    } catch (err) {
      setError(
        `${err.message} Verifique se a API está rodando em http://localhost:8000.`
      )
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="login-page">
        <form className="login-card" onSubmit={handleLogin}>
          <div className="login-brand-icon">
            <Bot size={30} />
          </div>

          <h1>Getnet</h1>
          <p className="login-subtitle">Multi-Agent AI</p>

          <div className="login-heading">
            <h2>Bem-vindo de volta</h2>
            <p>Entre com suas credenciais para continuar.</p>
          </div>

          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            type="text"
            value={loginUsername}
            onChange={(event) => setLoginUsername(event.target.value)}
            placeholder="Digite seu usuário"
            autoComplete="username"
            required
            disabled={loginLoading}
          />

          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            value={loginPassword}
            onChange={(event) => setLoginPassword(event.target.value)}
            placeholder="Digite sua senha"
            autoComplete="current-password"
            required
            disabled={loginLoading}
          />

          {loginError && (
            <div className="login-error">{loginError}</div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loginLoading}
          >
            {loginLoading ? 'Entrando...' : 'Entrar'}
          </button>

          <span className="login-footer">
            Ambiente seguro · Getnet Multi-Agent AI
          </span>
        </form>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Bot size={25} />
          </div>
          <div>
            <strong>Getnet</strong>
            <span>Multi-Agent AI</span>
          </div>
        </div>

        <div className="menu-label">MENU PRINCIPAL</div>

        <button
          className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveView('chat')}
        >
          <MessageSquare size={19} />
          <span>Chat inteligente</span>
        </button>

        <button
          className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveView('dashboard')}
        >
          <LayoutDashboard size={19} />
          <span>Dashboard</span>
        </button>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>Assistente disponível</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Getnet /</span>
            <strong>
              {activeView === 'chat'
                ? 'Chat inteligente'
                : 'Dashboard'}
            </strong>
          </div>

          <div className="topbar-user">
            <div className="avatar">
              <User size={18} />
            </div>
            <span>{username}</span>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
              title="Sair da conta"
            >
              <LogOut size={17} />
              Sair
            </button>
          </div>
        </header>

        {activeView === 'chat' ? (
          <section className="chat-page">
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  <Sparkles size={15} />
                  INTELIGÊNCIA ARTIFICIAL
                </div>
                <h1>Como podemos ajudar?</h1>
                <p>
                  Converse com os agentes inteligentes da Getnet.
                </p>
              </div>

              <div className="online-badge">
                <span />
                Sistema online
              </div>
            </div>

            <div className="chat-panel">
              <div className="chat-header">
                <div className="assistant-avatar">
                  <Bot size={22} />
                </div>
                <div>
                  <strong>Assistente Getnet</strong>
                  <span>Atendimento com múltiplos agentes</span>
                </div>
              </div>

              <div className="messages-area">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message-row ${
                      message.role === 'user' ? 'user-row' : ''
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="message-avatar">
                        {message.target_agent === 'human_handoff' ? (
                          <Headset size={17} />
                        ) : (
                          <Bot size={17} />
                        )}
                      </div>
                    )}

                    <div className="message-content">
                      <div className="message-bubble">
                        {message.content}
                      </div>

                      {message.role === 'assistant' &&
                        message.target_agent && (
                          <div className="message-meta">
                            <span>
                              Agente: {message.target_agent}
                            </span>

                            {message.tools_used?.length > 0 && (
                              <span>
                                <Wrench size={12} />
                                {message.tools_used.join(', ')}
                              </span>
                            )}

                            {message.token_usage?.total_tokens > 0 && (
                              <span>
                                {message.token_usage.total_tokens.toLocaleString('pt-BR')} tokens
                              </span>
                            )}
                          </div>
                        )}
                    </div>

                    {message.role === 'user' && (
                      <div className="user-avatar">
                        <User size={16} />
                      </div>
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="message-row">
                    <div className="message-avatar">
                      <Bot size={17} />
                    </div>
                    <div className="message-bubble typing">
                      Consultando os agentes...
                    </div>
                  </div>
                )}

                {error && (
                  <div className="error-message">{error}</div>
                )}
              </div>

              <div className="suggestions">
                <span>Experimente perguntar:</span>

                <button
                  onClick={() =>
                    sendMessage('Quais são as soluções da Getnet?')
                  }
                >
                  Soluções Getnet
                </button>

                <button
                  onClick={() =>
                    sendMessage('Como consultar minhas vendas?')
                  }
                >
                  Consultar vendas
                </button>

                <button
                  onClick={() =>
                    sendMessage('Quando recebo meus pagamentos?')
                  }
                >
                  Data de pagamento
                </button>
              </div>

              <form
                className="chat-input-area"
                onSubmit={(event) => {
                  event.preventDefault()
                  sendMessage()
                }}
              >
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Digite sua pergunta..."
                  maxLength={2000}
                  disabled={loading}
                />

                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                >
                  <Send size={18} />
                  Enviar
                </button>
              </form>

              <div className="input-caption">
                Getnet Multi-Agent · Respostas geradas por inteligência artificial
              </div>
            </div>
          </section>
        ) : (
          <section className="dashboard-page">
            <div className="page-heading">
              <div>
                <div className="eyebrow">
                  <Activity size={15} />
                  VISÃO GERAL
                </div>
                <h1>Dashboard</h1>
                <p>
                  Acompanhe a atividade desta sessão de demonstração.
                </p>
              </div>
            </div>

            <div className="metrics-grid">
              <MetricCard
                title="Perguntas enviadas"
                value={userMessages.length}
                icon={<MessageSquare size={21} />}
              />

              <MetricCard
                title="Respostas dos agentes"
                value={assistantMessages.length}
                icon={<Bot size={21} />}
              />

              <MetricCard
                title="Agentes utilizados"
                value={agentsUsed}
                icon={<Activity size={21} />}
              />

              <MetricCard
                title="Ferramentas acionadas"
                value={toolsUsed}
                icon={<Wrench size={21} />}
              />

              <MetricCard
                title="Tokens de entrada"
                value={tokenUsage.input_tokens.toLocaleString('pt-BR')}
                icon={<Activity size={21} />}
              />

              <MetricCard
                title="Tokens de saída"
                value={tokenUsage.output_tokens.toLocaleString('pt-BR')}
                icon={<Sparkles size={21} />}
              />

              <MetricCard
                title="Total de tokens"
                value={tokenUsage.total_tokens.toLocaleString('pt-BR')}
                icon={<Activity size={21} />}
              />
            </div>

            <div className="dashboard-card">
              <h2>Atividade recente</h2>

              {userMessages.length === 0 ? (
                <p className="empty-state">
                  Ainda não há perguntas nesta sessão. Comece uma
                  conversa no chat.
                </p>
              ) : (
                <div className="activity-list">
                  {userMessages
                    .slice()
                    .reverse()
                    .map((message) => (
                      <div
                        className="activity-item"
                        key={message.id}
                      >
                        <div className="activity-icon">
                          <MessageSquare size={17} />
                        </div>
                        <div>
                          <strong>{message.content}</strong>
                          <span>
                            Pergunta enviada ao assistente
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>

            <p className="dashboard-note">
              Os indicadores são calculados com base nas mensagens
              desta sessão no navegador. Eles não representam o
              histórico completo do banco de dados.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

function MetricCard({ title, value, icon }) {
  return (
    <div className="metric-card">
      <div className="metric-icon">{icon}</div>
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  )
}

export default App
