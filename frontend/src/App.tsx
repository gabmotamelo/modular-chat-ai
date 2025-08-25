import React, { useMemo, useRef, useState } from 'react'

type ChatMessage = {
  id: string
  who: 'user' | 'bot'
  text: string
  meta?: string
  agent?: 'RouterAgent'|'MathAgent'|'KnowledgeAgent'
}

type Conversation = {
  id: string
  title: string
  messages: ChatMessage[]
}

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8080'
function uid(){ return Math.random().toString(36).slice(2,9) }

export default function App(){
  const [convs, setConvs] = useState<Conversation[]>([{
    id: 'conv-' + uid(),
    title: 'Nova conversa',
    messages: []
  }])
  const [current, setCurrent] = useState(0)
  const [input, setInput] = useState('')
  const [userId] = useState('client-web')
  const [busy, setBusy] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)

  const conv = convs[current]

  function newConversation(){
    setConvs(prev => [{ id: 'conv-' + uid(), title: 'Nova conversa', messages: [] }, ...prev])
    setCurrent(0)
  }

  async function send(){
    const msg = input.trim()
    if(!msg || busy) return
    setBusy(true); setInput('')

    const userMsg: ChatMessage = { id: uid(), who:'user', text: msg }
    setConvs(prev => prev.map((c,i)=> i===current? ({...c, messages:[...c.messages, userMsg]}):c))

    try{
      const res = await fetch(API_URL + '/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ message: msg, user_id: userId, conversation_id: conv.id })
      })
      if(!res.ok) throw new Error('HTTP '+res.status)
      const data = await res.json()

      const agent = Array.isArray(data.agent_workflow) && data.agent_workflow.length
        ? data.agent_workflow[data.agent_workflow.length - 1].agent
        : 'KnowledgeAgent'

      const botMsg: ChatMessage = { id: uid(), who:'bot', text: data.response ?? '(sem resposta)', meta: data.source_agent_response ?? '', agent }
      setConvs(prev => prev.map((c,i)=> i===current? ({...c, messages:[...c.messages, botMsg]}):c))

      setTimeout(()=>{ listRef.current?.scrollTo({ top: 1e9, behavior:'smooth' }) }, 50)
    }catch(err:any){
      const botMsg: ChatMessage = { id: uid(), who:'bot', text: 'Falha ao falar com o backend. Verifique a API.', meta: err?.message, agent: 'RouterAgent' }
      setConvs(prev => prev.map((c,i)=> i===current? ({...c, messages:[...c.messages, botMsg]}):c))
    }finally{
      setBusy(false)
    }
  }

  function renderAgentTag(a?: ChatMessage['agent']){
    if(a === 'MathAgent') return <span className="tag math">MathAgent</span>
    if(a === 'KnowledgeAgent') return <span className="tag knowledge">KnowledgeAgent</span>
    if(a === 'RouterAgent') return <span className="tag router">Router</span>
    return null
  }

  return (
    <div className="container">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">∞</div>
          <div>
            <div className="title">InfinitePay</div>
            <div className="badge">Modular Chatbot</div>
          </div>
        </div>

        <div className="new-conv">
          <button className="button" onClick={newConversation}>+ Nova</button>
        </div>

        <div className="list scroll" style={{minHeight:0}}>
          {convs.map((c, i) => (
            <div key={c.id} className={'item ' + (i===current ? 'active' : '')} onClick={() => setCurrent(i)}>
              <span>{c.title}</span>
              <span className="badge" title={c.id}>{c.id.slice(0,10)}</span>
            </div>
          ))}
        </div>
        <div style={{marginTop:'auto', fontSize:'.8rem', color:'#9AA6B2'}}>
          API: <code>{API_URL}</code>
        </div>
      </aside>

      <main className="main">
        <div className="header">
          <div>
            <div style={{fontSize:'1.1rem', fontWeight:700}}>Conversa</div>
            <div className="meta">ID: <code>{conv.id}</code></div>
          </div>
          <div style={{display:'flex', gap:'.5rem'}}>
            <span className="tag router">Router</span>
            <span className="tag knowledge">Knowledge</span>
            <span className="tag math">Math</span>
          </div>
        </div>

        <div className="card">
          <div className="history scroll" ref={listRef}>
            {conv.messages.length === 0 && (
              <div className="meta">
                Envie uma mensagem para começar. Exemplos: <em>"Quais são as taxas da maquininha?"</em>, <em>"65 x 3.11"</em>
              </div>
            )}
            {conv.messages.map(m => (
              <div key={m.id} className={'msg ' + m.who}>
                <div className="who">{m.who === 'user' ? 'Você' : 'Bot'}</div>
                <div className="bubble">
                  <div>{m.text}</div>
                  <div className="meta">
                    {renderAgentTag(m.agent)}
                    {m.meta ? <><span>•</span><span>{m.meta}</span></> : null}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="footer">
            <input
              className="input"
              placeholder="Digite sua mensagem..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if(e.key === 'Enter') send() }}
              style={{flex:1}}
            />
            <button className="button" onClick={send} disabled={busy}>Enviar</button>
          </div>
        </div>
      </main>
    </div>
  )
}
