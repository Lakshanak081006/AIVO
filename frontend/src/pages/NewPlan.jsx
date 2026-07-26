import {useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {api} from '../api/client'
import VoiceInput from '../components/VoiceInput'
import {ErrorBox, Spinner} from '../components/Common'

const PLAN_BG = 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80'
const examples = [
  'Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums.',
  'Plan a three-day trip from Coimbatore to Mumbai for two people next weekend under ₹15000.',
  'Plan a weekend trip from Coimbatore to Bengaluru for three people under ₹25000.',
]
const AGENTS = ['Requirement','Planner','Transport','Hotel','Weather','Attraction','Itinerary','Budget','Alternative','Replanning']

export default function NewPlan() {
  const [instruction, setInstruction] = useState(examples[0])
  const [language, setLanguage] = useState('English')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState()
  const [clarify, setClarify] = useState(null)
  const [answer, setAnswer] = useState('')
  const nav = useNavigate()

  const submit = async () => {
    setLoading(true); setError(null)
    try {
      const r = await api.post('/travel/plan', {instruction, response_language: language})
      if (r.data.status === 'clarification_required') setClarify(r.data)
      else nav(`/plans/${r.data.plan_id}`)
    } catch(e) { setError(e) }
    finally { setLoading(false) }
  }

  const respond = async () => {
    setLoading(true)
    try {
      const r = await api.post('/travel/clarify', {request_id: clarify.request_id, answer})
      if (r.data.status === 'clarification_required') setClarify(r.data)
      else nav(`/plans/${r.data.plan_id}`)
    } catch(e) { setError(e) }
    finally { setLoading(false) }
  }

  if (loading) return <Spinner/>

  return (
    <>
      {/* Page hero */}
      <div className="page-hero" style={{backgroundImage:`url(${PLAN_BG})`}}>
        <div className="page-hero-overlay">
          <span className="eyebrow" style={{color:'#a8c4ff'}}>NEW TRIP</span>
          <h2 style={{margin:'8px 0 6px',color:'#fff',fontSize:26}}>Plan your next trip</h2>
          <p style={{color:'#c8d8ff',margin:0}}>Describe your trip and AIVA will coordinate transport, stay, weather, activities and budget.</p>
        </div>
      </div>

      <div className="two-col" style={{marginTop:20}}>
        <div className="panel">
          <label>Response language
            <select value={language} onChange={e=>setLanguage(e.target.value)}>
              <option>English</option><option>Tamil</option><option>Hindi</option>
            </select>
          </label>
          <label>High-level instruction
            <textarea rows="7" value={instruction} onChange={e=>setInstruction(e.target.value)}/>
          </label>
          <VoiceInput value={instruction} onChange={setInstruction} language={language==='Tamil'?'ta-IN':language==='Hindi'?'hi-IN':'en-IN'}/>
          <ErrorBox error={error}/>
          <button className="primary" onClick={submit} style={{width:'100%',marginTop:8,padding:'12px'}}>
            Generate Trip Plan
          </button>
        </div>

        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          {/* Example instructions */}
          <div className="panel">
            <h3 style={{margin:'0 0 14px',fontSize:15}}>Example instructions</h3>
            {examples.map(x=>(
              <button key={x} className="example" onClick={()=>setInstruction(x)} style={{marginBottom:8}}>
                {x}
              </button>
            ))}
          </div>

          {/* Agents panel with image */}
          <div className="panel" style={{padding:0,overflow:'hidden'}}>
            <img src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=600&q=70" alt="agents" style={{width:'100%',height:110,objectFit:'cover'}}/>
            <div style={{padding:'16px 20px'}}>
              <h3 style={{margin:'0 0 12px',fontSize:15}}>Agents that will run</h3>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6}}>
                {AGENTS.map(x=>(
                  <span key={x} style={{fontSize:12,fontWeight:600,color:'var(--blue)',background:'#eef2ff',padding:'5px 10px',borderRadius:6}}>
                    {x}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {clarify && (
        <div className="modal-back">
          <div className="modal">
            <h3>Clarification required</h3>
            <p>{clarify.question}</p>
            <p className="muted">Missing: {clarify.missing_fields.join(', ')}</p>
            <textarea rows="4" value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="Enter the missing details"/>
            <button onClick={respond} style={{width:'100%',marginTop:8}}>Continue workflow</button>
          </div>
        </div>
      )}
    </>
  )
}
